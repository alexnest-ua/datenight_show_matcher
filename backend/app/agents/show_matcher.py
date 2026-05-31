"""Sub-agent #3 — Show Matcher  (analytical / Sonnet tier).

Given the psychographic profile (and any off-limits titles from a previous
re-pick), proposes ranked date-night candidates. Candidate metadata (year/genres)
is enriched from the local catalog so the UI cards are complete even when the
model omits it.
"""

from __future__ import annotations

from app.data_access.catalog import lookup
from app.llm.provider import LLMProvider
from app.models import InterestProfile, ShowCandidate


def _enrich(candidate: ShowCandidate) -> ShowCandidate:
    entry = lookup(candidate.title)
    if entry is None:
        return candidate
    if candidate.year is None:
        candidate.year = entry.year
    if not candidate.genres:
        candidate.genres = list(entry.genres)
    return candidate


async def match_shows(
    profile: InterestProfile,
    provider: LLMProvider,
    *,
    handle: str,
    off_limits: list[str],
    attempt: int,
    n: int = 3,
) -> list[ShowCandidate]:
    candidates = await provider.match_shows(
        profile, handle=handle, off_limits=off_limits, attempt=attempt, n=n
    )
    return [_enrich(c) for c in candidates]
