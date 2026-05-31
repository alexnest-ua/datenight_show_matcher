"""Sub-agent #4 — Streaming Checker  (fast / Haiku tier + MCP tool).

Verifies each candidate against the user's OWN subscriptions using the local MCP
server's ``check_availability`` tool.

  * REAL mode: a genuine Anthropic tool-use loop — Claude decides to call the MCP
    tool for each title (function calling). We capture the raw tool results and
    backfill any title the model skipped, so coverage is guaranteed.
  * MOCK mode: no LLM — we call the same MCP tool directly.

Either way the MCP server is the single source of truth, and the user-subscription
filter (Netflix/HBO only; Prime ignored) is applied here in code — never trusted
to the model's prose.
"""

from __future__ import annotations

import json

from app.agents.prompts import STREAMING_CHECKER_SYSTEM, streaming_checker_user_prompt
from app.config import RunMode, Settings
from app.llm.anthropic_client import build_async_client, run_tool_loop
from app.mcp_server.client import MCPCatalogClient
from app.models import Availability, ShowCandidate


def _to_availability(title: str, raw: dict, user_platforms: set[str]) -> Availability:
    all_platforms = [p.lower() for p in raw.get("platforms", [])]
    user_subset = [p for p in all_platforms if p in user_platforms]
    return Availability(
        title=title,
        found=bool(raw.get("found")),
        available=bool(user_subset),
        platforms=user_subset,
        all_platforms=all_platforms,
    )


async def check_availability(
    candidates: list[ShowCandidate], settings: Settings
) -> list[Availability]:
    if not candidates:
        return []

    user_platforms = {p.lower() for p in settings.user_platforms}
    titles = [c.title for c in candidates]
    raw_by_title: dict[str, dict] = {}

    async with MCPCatalogClient(settings) as mcp:
        if settings.effective_mode is RunMode.REAL:
            client = build_async_client(settings)

            async def executor(name: str, tool_input: dict) -> tuple[str, dict]:
                raw = await mcp.call(name, tool_input)
                requested = (tool_input.get("title") or "").strip().lower()
                if requested:
                    raw_by_title[requested] = raw
                returned = str(raw.get("title", "")).strip().lower()
                if returned:
                    raw_by_title[returned] = raw
                return json.dumps(raw), raw

            await run_tool_loop(
                client,
                model=settings.model_fast,
                system=STREAMING_CHECKER_SYSTEM,
                user=streaming_checker_user_prompt(titles),
                tools=mcp.anthropic_tools(),
                executor=executor,
            )

        # Guarantee every candidate was actually checked (mock path does it all
        # here; real path only backfills titles the model didn't call).
        for candidate in candidates:
            key = candidate.title.strip().lower()
            if key not in raw_by_title:
                raw_by_title[key] = await mcp.check(candidate.title)

    return [
        _to_availability(c.title, raw_by_title.get(c.title.strip().lower(), {}), user_platforms)
        for c in candidates
    ]
