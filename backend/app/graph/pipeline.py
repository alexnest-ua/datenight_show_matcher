"""The orchestrator: a LangGraph StateGraph wiring the four sub-agents.

    START → insta_reader → interest_profiler → show_matcher → streaming_checker
                                                   ↑                  │
                                                   └──── repick ──────┘  (capped)
                                                                      └── done/give_up → END

`run_pipeline` is an async generator of `PipelineEvent`s: it emits the run-level
events itself and stamps each node's `get_stream_writer` event with a monotonic
`seq` + `elapsed_ms`. The same generator powers the CLI, the SSE endpoint, and
the demo-fixture recorder — one core, three surfaces.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from typing import TypedDict

from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph

from app.agents.insta_reader import read_profile
from app.agents.interest_profiler import build_profile
from app.agents.show_matcher import match_shows
from app.agents.streaming_checker import check_availability
from app.config import Settings, get_settings
from app.llm.provider import build_provider
from app.models import (
    EventType,
    ExcludedShow,
    FinalPick,
    InterestProfile,
    PipelineEvent,
    ProfileDump,
    RunResult,
    ShowCandidate,
)

TARGET_PICKS = 3

# Simulated per-stage latency in MOCK mode so the offline demo (and its recorded
# fixtures) feel lifelike instead of finishing in microseconds. Real mode uses
# actual API latency.
MOCK_DELAYS = {
    "insta_reader": 0.6,
    "interest_profiler": 1.1,
    "show_matcher": 1.0,
    "streaming_checker": 0.8,
}


class PipelineState(TypedDict, total=False):
    handle: str
    user_platforms: list[str]
    target: int
    attempt: int
    max_attempts: int
    dump: ProfileDump
    profile: InterestProfile
    candidates: list[ShowCandidate]
    accepted: list[FinalPick]
    excluded: list[ExcludedShow]
    excluded_titles: list[str]
    last_excluded: list[ExcludedShow]


def _emit(**payload: object) -> None:
    """Emit a partial event from inside a node (orchestrator stamps seq/time)."""
    try:
        writer = get_stream_writer()
    except Exception:  # pragma: no cover - outside a streaming run
        writer = None
    if writer:
        writer(payload)


def build_graph(provider, settings: Settings):
    is_mock = settings.is_mock

    async def insta_node(state: PipelineState) -> dict:
        _emit(event="stage_started", stage="insta_reader",
              message=f"Reading {state['handle']}'s profile…")
        if is_mock:
            await asyncio.sleep(MOCK_DELAYS["insta_reader"])
        dump = await read_profile(state["handle"], settings)
        _emit(event="stage_completed", stage="insta_reader",
              message=f"Read {len(dump.posts)} posts · {len(dump.hashtags)} hashtags",
              data=dump.model_dump())
        return {"dump": dump}

    async def profiler_node(state: PipelineState) -> dict:
        _emit(event="stage_started", stage="interest_profiler",
              message="Analysing interests & vibe…")
        if is_mock:
            await asyncio.sleep(MOCK_DELAYS["interest_profiler"])
        try:
            profile = await build_profile(state["dump"], provider)
        except Exception as exc:
            _emit(event="stage_failed", stage="interest_profiler",
                  message=str(exc), data={"error": str(exc)})
            raise
        _emit(event="stage_completed", stage="interest_profiler",
              message="Built psychographic profile", data=profile.model_dump())
        return {"profile": profile}

    async def matcher_node(state: PipelineState) -> dict:
        attempt = state.get("attempt", 0) + 1
        if attempt > 1:
            _emit(event="repick", stage="show_matcher", attempt=attempt,
                  message="A pick wasn't on your subscriptions — re-picking",
                  data={"excluded": [e.model_dump() for e in state.get("last_excluded", [])]})
        _emit(event="stage_started", stage="show_matcher", attempt=attempt,
              message="Matching date-night shows…")
        if is_mock:
            await asyncio.sleep(MOCK_DELAYS["show_matcher"])
        accepted = state.get("accepted", [])
        off_limits = list(state.get("excluded_titles", [])) + [p.title for p in accepted]
        try:
            candidates = await match_shows(
                state["profile"], provider,
                handle=state["handle"], off_limits=off_limits, attempt=attempt, n=TARGET_PICKS,
            )
        except Exception as exc:
            _emit(event="stage_failed", stage="show_matcher", attempt=attempt,
                  message=str(exc), data={"error": str(exc)})
            raise
        _emit(event="stage_completed", stage="show_matcher", attempt=attempt,
              message=f"{len(candidates)} candidate(s) proposed",
              data={"candidates": [c.model_dump() for c in candidates]})
        return {"candidates": candidates, "attempt": attempt}

    async def checker_node(state: PipelineState) -> dict:
        attempt = state.get("attempt", 1)
        candidates = state.get("candidates", [])
        subs = ", ".join(p.upper() for p in state.get("user_platforms", []))
        _emit(event="stage_started", stage="streaming_checker", attempt=attempt,
              message=f"Checking availability on {subs} (via MCP tool)…")
        if is_mock:
            await asyncio.sleep(MOCK_DELAYS["streaming_checker"])
        try:
            results = await check_availability(candidates, settings)
        except Exception as exc:
            _emit(event="stage_failed", stage="streaming_checker", attempt=attempt,
                  message=str(exc), data={"error": str(exc)})
            raise
        n_avail = sum(1 for r in results if r.available)
        _emit(event="stage_completed", stage="streaming_checker", attempt=attempt,
              message=f"{n_avail}/{len(results)} available on your subscriptions",
              data={"results": [r.model_dump() for r in results]})

        target = state.get("target", TARGET_PICKS)
        accepted = list(state.get("accepted", []))
        accepted_titles = {p.title.strip().lower() for p in accepted}
        excluded = list(state.get("excluded", []))
        excluded_titles = list(state.get("excluded_titles", []))
        excluded_set = {t.strip().lower() for t in excluded_titles}
        last_excluded: list[ExcludedShow] = []

        for cand, res in zip(candidates, results, strict=True):
            key = cand.title.strip().lower()
            if res.available and len(accepted) < target and key not in accepted_titles:
                accepted.append(FinalPick(
                    title=cand.title, year=cand.year, genres=cand.genres,
                    why=cand.why, platforms=res.platforms,
                ))
                accepted_titles.add(key)
            elif not res.available and key not in excluded_set:
                if not res.found:
                    reason = "not found in the catalog"
                elif res.all_platforms:
                    reason = f"only on {', '.join(res.all_platforms)} (not subscribed)"
                else:
                    reason = "not available on any tracked platform"
                ex = ExcludedShow(title=cand.title, reason=reason)
                excluded.append(ex)
                last_excluded.append(ex)
                excluded_titles.append(cand.title)
                excluded_set.add(key)

        return {
            "accepted": accepted,
            "excluded": excluded,
            "excluded_titles": excluded_titles,
            "last_excluded": last_excluded,
        }

    def route(state: PipelineState) -> str:
        if len(state.get("accepted", [])) >= state.get("target", TARGET_PICKS):
            return "done"
        if state.get("attempt", 0) >= state.get("max_attempts", 1):
            return "give_up"
        return "repick"

    builder = StateGraph(PipelineState)
    builder.add_node("insta_reader", insta_node)
    builder.add_node("interest_profiler", profiler_node)
    builder.add_node("show_matcher", matcher_node)
    builder.add_node("streaming_checker", checker_node)
    builder.add_edge(START, "insta_reader")
    builder.add_edge("insta_reader", "interest_profiler")
    builder.add_edge("interest_profiler", "show_matcher")
    builder.add_edge("show_matcher", "streaming_checker")
    builder.add_conditional_edges(
        "streaming_checker", route,
        {"repick": "show_matcher", "done": END, "give_up": END},
    )
    return builder.compile()


async def run_pipeline(
    handle: str, settings: Settings | None = None
) -> AsyncIterator[PipelineEvent]:
    """Run the full pipeline, yielding PipelineEvents in order."""
    settings = settings or get_settings()
    provider = build_provider(settings)
    graph = build_graph(provider, settings)

    start = time.monotonic()
    seq = 0

    def make(event, *, stage=None, attempt=1, message="", data=None) -> PipelineEvent:
        nonlocal seq
        ev = PipelineEvent(
            seq=seq, event=event, stage=stage, attempt=attempt,
            elapsed_ms=int((time.monotonic() - start) * 1000),
            message=message, data=data,
        )
        seq += 1
        return ev

    yield make(
        EventType.RUN_STARTED,
        message=f"Finding tonight's show for {handle}…",
        data={"username": handle, "mode": provider.mode.value,
              "user_platforms": settings.user_platforms},
    )

    init: PipelineState = {
        "handle": handle,
        "user_platforms": settings.user_platforms,
        "target": TARGET_PICKS,
        "attempt": 0,
        "max_attempts": settings.max_repicks + 1,
        "candidates": [],
        "accepted": [],
        "excluded": [],
        "excluded_titles": [],
        "last_excluded": [],
    }
    recursion_limit = (settings.max_repicks + 1) * 3 + 10
    final_state: dict | None = None

    try:
        async for mode, chunk in graph.astream(
            init, stream_mode=["custom", "values"],
            config={"recursion_limit": recursion_limit},
        ):
            if mode == "custom":
                yield make(
                    chunk["event"], stage=chunk.get("stage"),
                    attempt=chunk.get("attempt", 1),
                    message=chunk.get("message", ""), data=chunk.get("data"),
                )
            elif mode == "values":
                final_state = chunk
    except Exception as exc:  # noqa: BLE001 - surface any failure as an event
        yield make(EventType.RUN_FAILED, message=f"Pipeline failed: {exc}",
                   data={"error": str(exc)})
        return

    if not final_state or "profile" not in final_state:
        yield make(EventType.RUN_FAILED, message="Pipeline produced no result",
                   data={"error": "incomplete pipeline state"})
        return

    result = RunResult(
        username=handle,
        mode=provider.mode.value,
        profile=final_state["profile"],
        picks=final_state.get("accepted", []),
        excluded=final_state.get("excluded", []),
        attempts=final_state.get("attempt", 1),
        user_platforms=settings.user_platforms,
    )
    yield make(EventType.RUN_COMPLETED, message="Tonight's lineup is ready",
               data=result.model_dump())


async def run_pipeline_to_result(handle: str, settings: Settings | None = None) -> RunResult:
    """Convenience: run to completion and return just the RunResult."""
    result: RunResult | None = None
    async for ev in run_pipeline(handle, settings):
        if ev.event is EventType.RUN_COMPLETED and ev.data:
            result = RunResult(**ev.data)
        elif ev.event is EventType.RUN_FAILED:
            msg = ev.data.get("error") if isinstance(ev.data, dict) else "pipeline failed"
            raise RuntimeError(msg or "pipeline failed")
    if result is None:
        raise RuntimeError("pipeline produced no result")
    return result
