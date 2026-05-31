"""Thin async wrapper around the Anthropic SDK.

Two helpers cover everything the agents need:
  * ``parse_json``  — strict, schema-validated JSON output (Profiler, Matcher).
  * ``run_tool_loop`` — a full agentic tool-use loop (Streaming Checker driving
    the MCP ``check_availability`` tool).

Prompt caching: we mark the (stable) system prompt with ``cache_control`` so that
across a run the prefix is reused. NOTE: our system prompts are well under the
per-model minimum cacheable prefix (2048 tok Sonnet / 4096 tok Haiku), so today
this is effectively a no-op the API silently ignores — it's wired correctly so it
starts paying off the moment the prompts grow. Verified via
``usage.cache_read_input_tokens``.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

import anthropic
from pydantic import BaseModel

from app.config import Settings

T = TypeVar("T", bound=BaseModel)

# executor(name, input_dict) -> (content_for_anthropic, raw_result_for_us)
ToolExecutor = Callable[[str, dict], Awaitable[tuple[Any, dict]]]


def build_async_client(settings: Settings) -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(
        api_key=settings.anthropic_api_key,
        max_retries=settings.max_retries,
        timeout=settings.request_timeout,
    )


def _system_block(system: str) -> list[dict]:
    return [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]


async def parse_json(
    client: anthropic.AsyncAnthropic,
    *,
    model: str,
    system: str,
    user: str,
    output_model: type[T],
    max_tokens: int = 2048,
) -> T:
    """Return a validated pydantic instance using the SDK's structured-output parse."""
    resp = await client.messages.parse(
        model=model,
        max_tokens=max_tokens,
        system=_system_block(system),
        messages=[{"role": "user", "content": user}],
        output_format=output_model,
    )
    parsed = resp.parsed_output
    if parsed is None:  # pragma: no cover - defensive
        raise RuntimeError(f"{output_model.__name__}: model returned no parseable output")
    return parsed


async def run_tool_loop(
    client: anthropic.AsyncAnthropic,
    *,
    model: str,
    system: str,
    user: str,
    tools: list[dict],
    executor: ToolExecutor,
    max_tokens: int = 2048,
    max_iters: int = 12,
) -> tuple[str, list[dict]]:
    """Run a manual tool-use loop.

    Returns ``(final_text, captured_results)`` where ``captured_results`` is the
    list of raw tool-result dicts we executed (the authoritative data the caller
    uses — we never trust the model's prose for ground truth).
    """
    messages: list[dict] = [{"role": "user", "content": user}]
    captured: list[dict] = []

    for _ in range(max_iters):
        resp = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=_system_block(system),
            tools=tools,
            messages=messages,
        )

        if resp.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": resp.content})
            tool_results = []
            for block in resp.content:
                if getattr(block, "type", None) == "tool_use":
                    content, raw = await executor(block.name, dict(block.input))
                    captured.append(raw)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": content,
                        }
                    )
            messages.append({"role": "user", "content": tool_results})
            continue

        if resp.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": resp.content})
            continue

        text = "".join(
            b.text for b in resp.content if getattr(b, "type", None) == "text"
        )
        return text, captured

    return "", captured
