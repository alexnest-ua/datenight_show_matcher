"""LLM provider abstraction.

The analytical agents (Profiler, Matcher) talk to an ``LLMProvider`` rather than
to the Anthropic SDK directly, so the exact same pipeline runs either against the
real Claude API or against a deterministic offline mock — no key, no cost, fully
reproducible (which is also what the test-suite and the demo fixtures rely on).

The Streaming Checker is intentionally NOT part of this abstraction: it always
goes through the real MCP server (see ``app.agents.streaming_checker``).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import anthropic

from app.agents.prompts import (
    INTEREST_PROFILER_SYSTEM,
    SHOW_MATCHER_SYSTEM,
    show_matcher_user_prompt,
)
from app.config import RunMode, Settings
from app.llm.anthropic_client import build_async_client, parse_json
from app.mock_data.fixtures import get_script
from app.models import InterestProfile, ProfileDump, ShowCandidate, ShowMatch


class LLMProvider(ABC):
    mode: RunMode

    @abstractmethod
    async def profile_interests(self, dump: ProfileDump) -> InterestProfile: ...

    @abstractmethod
    async def match_shows(
        self,
        profile: InterestProfile,
        *,
        handle: str,
        off_limits: list[str],
        attempt: int,
        n: int = 3,
    ) -> list[ShowCandidate]: ...


def _drop_off_limits(cands: list[ShowCandidate], off_limits: list[str]) -> list[ShowCandidate]:
    banned = {t.strip().lower() for t in off_limits}
    return [c for c in cands if c.title.strip().lower() not in banned]


class RealProvider(LLMProvider):
    mode = RunMode.REAL

    def __init__(self, settings: Settings):
        self._settings = settings
        self._client: anthropic.AsyncAnthropic = build_async_client(settings)

    async def profile_interests(self, dump: ProfileDump) -> InterestProfile:
        return await parse_json(
            self._client,
            model=self._settings.model_analysis,
            system=INTEREST_PROFILER_SYSTEM,
            user=dump.to_text(),
            output_model=InterestProfile,
        )

    async def match_shows(
        self,
        profile: InterestProfile,
        *,
        handle: str,
        off_limits: list[str],
        attempt: int,
        n: int = 3,
    ) -> list[ShowCandidate]:
        match = await parse_json(
            self._client,
            model=self._settings.model_analysis,
            system=SHOW_MATCHER_SYSTEM,
            user=show_matcher_user_prompt(
                profile.model_dump_json(indent=2), off_limits, n=n
            ),
            output_model=ShowMatch,
        )
        # Defend against a model re-suggesting a banned title.
        return _drop_off_limits(match.picks, off_limits)


class MockProvider(LLMProvider):
    """Deterministic, key-free provider backed by app.mock_data.fixtures."""

    mode = RunMode.MOCK

    def __init__(self, settings: Settings):
        self._settings = settings

    async def profile_interests(self, dump: ProfileDump) -> InterestProfile:
        return get_script(dump.handle).interest

    async def match_shows(
        self,
        profile: InterestProfile,
        *,
        handle: str,
        off_limits: list[str],
        attempt: int,
        n: int = 3,
    ) -> list[ShowCandidate]:
        attempts = get_script(handle).attempts
        cands = attempts[attempt - 1] if 0 <= attempt - 1 < len(attempts) else []
        return _drop_off_limits(list(cands), off_limits)


def build_provider(settings: Settings) -> LLMProvider:
    if settings.effective_mode is RunMode.REAL:
        return RealProvider(settings)
    return MockProvider(settings)
