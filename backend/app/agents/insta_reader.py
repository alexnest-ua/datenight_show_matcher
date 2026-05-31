"""Sub-agent #1 — Insta Reader  (mock by default; optional Haiku-tier path).

Per the assignment there is NO real Instagram scraping. By default this returns
a pre-baked dump for the handle. With INSTA_READER_USE_LLM=true (and a real key)
it routes the raw dump through the cheap fast model to "normalise" it — a faithful
demonstration of using a light model for a routine task.
"""

from __future__ import annotations

from app.config import RunMode, Settings
from app.mock_data.profiles import get_profile
from app.models import ProfileDump


async def read_profile(handle: str, settings: Settings) -> ProfileDump:
    dump = get_profile(handle)

    if settings.insta_reader_use_llm and settings.effective_mode is RunMode.REAL:
        from app.agents.prompts import INSTA_READER_SYSTEM, instagram_dump_block
        from app.llm.anthropic_client import build_async_client, parse_json

        client = build_async_client(settings)
        normalized = await parse_json(
            client,
            model=settings.model_fast,
            system=INSTA_READER_SYSTEM,
            user=instagram_dump_block(dump.to_text()),
            output_model=ProfileDump,
            max_tokens=1024,
        )
        normalized.handle = dump.handle or normalized.handle
        return normalized

    return dump
