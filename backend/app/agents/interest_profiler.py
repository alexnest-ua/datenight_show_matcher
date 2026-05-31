"""Sub-agent #2 — Interest Profiler  (analytical / Sonnet tier).

Turns the raw profile dump into a strict-JSON psychographic profile. The prompt
and model live in the provider; this module is the agent's stable entry point.
"""

from __future__ import annotations

from app.llm.provider import LLMProvider
from app.models import InterestProfile, ProfileDump


async def build_profile(dump: ProfileDump, provider: LLMProvider) -> InterestProfile:
    return await provider.profile_interests(dump)
