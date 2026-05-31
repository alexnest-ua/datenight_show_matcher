"""Shared data contracts for the whole system.

These pydantic models are the single source of truth used by:
  - the four sub-agents (strict JSON output schemas),
  - the LangGraph pipeline state,
  - the CLI renderer,
  - the FastAPI SSE stream,
  - and (mirrored in TypeScript) the React frontend.

The ``PipelineEvent`` model in particular is the wire contract for the SSE
stream and the bundled "recorded-run" demo fixtures — see docs/contracts.md.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────
# Stage 1 — Insta Reader output (raw profile dump, no scraping)
# ─────────────────────────────────────────────────────────────


class ProfileDump(BaseModel):
    """Raw, unstructured-ish text scraped from a profile (mocked)."""

    handle: str
    display_name: str = ""
    bio: str = ""
    posts: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)

    def to_text(self) -> str:
        """Flatten to the plain text dump the Profiler agent consumes."""
        lines = [f"Handle: {self.handle}"]
        if self.display_name:
            lines.append(f"Display name: {self.display_name}")
        if self.bio:
            lines.append(f"Bio: {self.bio}")
        if self.posts:
            lines.append("Recent post captions:")
            lines.extend(f"  - {p}" for p in self.posts)
        if self.hashtags:
            lines.append("Hashtags: " + " ".join(f"#{h.lstrip('#')}" for h in self.hashtags))
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Stage 2 — Interest Profiler output (strict JSON, per the PDF)
# ─────────────────────────────────────────────────────────────


class InterestProfile(BaseModel):
    """Psychographic profile. Field names match the assignment's prompt exactly."""

    primary_interests: list[str] = Field(..., description="3-5 core interests")
    aesthetic_vibe: str = Field(..., description="short description of style/vibe")
    recommended_genres: list[str] = Field(..., description="2-4 TV/film genres")


# ─────────────────────────────────────────────────────────────
# Stage 3 — Show Matcher output (top-3 candidates with reasoning)
# ─────────────────────────────────────────────────────────────


class ShowCandidate(BaseModel):
    title: str
    year: int | None = None
    genres: list[str] = Field(default_factory=list)
    why: str = Field(..., description="Why this fits the date / her vibe")


class ShowMatch(BaseModel):
    picks: list[ShowCandidate] = Field(..., description="Exactly 3, ranked best-first")


# ─────────────────────────────────────────────────────────────
# Stage 4 — Streaming Checker output (availability via MCP tool)
# ─────────────────────────────────────────────────────────────


class Availability(BaseModel):
    """Result of one MCP `check_availability` lookup (already filtered to the
    user's subscriptions by the checker)."""

    title: str
    found: bool = False
    available: bool = False
    platforms: list[str] = Field(default_factory=list, description="subset of the user's subs")
    all_platforms: list[str] = Field(default_factory=list, description="every platform it's on")


class FinalPick(BaseModel):
    title: str
    year: int | None = None
    genres: list[str] = Field(default_factory=list)
    why: str
    platforms: list[str] = Field(
        ..., description="user subscriptions it streams on, e.g. [netflix]"
    )


class ExcludedShow(BaseModel):
    title: str
    reason: str


# ─────────────────────────────────────────────────────────────
# Final run result
# ─────────────────────────────────────────────────────────────


class RunResult(BaseModel):
    username: str
    mode: str = Field(..., description="real | mock")
    profile: InterestProfile
    picks: list[FinalPick] = Field(default_factory=list)
    excluded: list[ExcludedShow] = Field(default_factory=list)
    attempts: int = 1
    user_platforms: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# SSE / pipeline-event wire contract  (mirrored in TS frontend)
# ─────────────────────────────────────────────────────────────


class EventType(StrEnum):
    RUN_STARTED = "run_started"
    STAGE_STARTED = "stage_started"
    STAGE_PROGRESS = "stage_progress"
    STAGE_COMPLETED = "stage_completed"
    STAGE_FAILED = "stage_failed"
    REPICK = "repick"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"


class Stage(StrEnum):
    INSTA_READER = "insta_reader"
    INTEREST_PROFILER = "interest_profiler"
    SHOW_MATCHER = "show_matcher"
    STREAMING_CHECKER = "streaming_checker"


# Human-facing labels for each stage (used by CLI + UI; kept here so both agree).
STAGE_LABELS: dict[str, str] = {
    Stage.INSTA_READER.value: "Insta Reader",
    Stage.INTEREST_PROFILER.value: "Interest Profiler",
    Stage.SHOW_MATCHER.value: "Show Matcher",
    Stage.STREAMING_CHECKER.value: "Streaming Checker",
}

STAGE_ORDER: list[str] = [s.value for s in Stage]


class PipelineEvent(BaseModel):
    """One event emitted by the orchestrator.

    Serialized as the ``data:`` payload of an SSE frame (event name == ``event``)
    and stored verbatim in the recorded-run demo fixtures.
    """

    seq: int = Field(..., description="monotonic counter within a run, starts at 0")
    event: EventType
    stage: Stage | None = None
    attempt: int = Field(default=1, description="re-pick attempt this event belongs to")
    elapsed_ms: int = Field(default=0, description="ms since run start — drives demo replay timing")
    message: str = ""
    # Stage payloads (ProfileDump / InterestProfile / list[ShowCandidate] /
    # list[Availability]) and, on RUN_COMPLETED, the full RunResult — all as
    # plain JSON so the frontend can render without a schema per stage.
    data: dict | list | None = None
