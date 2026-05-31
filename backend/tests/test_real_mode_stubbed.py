"""Exercise the REAL-mode code paths without a real API key.

A stub Anthropic client (object-level fake) lets us drive the exact code that
runs when ANTHROPIC_API_KEY is set — `parse_json`, the tool-use loop, the
`RealProvider`, and the real-mode Streaming Checker over the *actual* MCP server
— so the one path the offline tests can't cover is still verified deterministically.
"""

from __future__ import annotations

import types

import app.agents.streaming_checker as sc_mod
import app.llm.provider as provider_mod
from app.agents.streaming_checker import check_availability
from app.config import RunMode, get_settings
from app.llm.anthropic_client import parse_json, run_tool_loop
from app.llm.provider import RealProvider
from app.models import (
    InterestProfile,
    ProfileDump,
    ShowCandidate,
    ShowMatch,
)


# ── Stub Anthropic SDK objects ───────────────────────────────
def _text_block(text: str):
    return types.SimpleNamespace(type="text", text=text)


def _tool_use_block(name: str, tool_input: dict, block_id: str = "tu_1"):
    return types.SimpleNamespace(type="tool_use", name=name, input=tool_input, id=block_id)


def _resp_tool_use(blocks):
    return types.SimpleNamespace(stop_reason="tool_use", content=blocks)


def _resp_end_turn(text: str):
    return types.SimpleNamespace(stop_reason="end_turn", content=[_text_block(text)])


class _FakeMessages:
    def __init__(self, parse_result=None, create_script=None):
        self._parse_result = parse_result
        self._create_script = list(create_script or [])
        self.parse_calls = 0
        self.create_calls = 0

    async def parse(self, **_kwargs):
        self.parse_calls += 1
        return types.SimpleNamespace(parsed_output=self._parse_result)

    async def create(self, **_kwargs):
        self.create_calls += 1
        if self._create_script:
            return self._create_script.pop(0)
        return _resp_end_turn("done")


class _FakeClient:
    def __init__(self, parse_result=None, create_script=None):
        self.messages = _FakeMessages(parse_result=parse_result, create_script=create_script)


# ── anthropic_client helpers ─────────────────────────────────
async def test_parse_json_returns_validated_model():
    profile = InterestProfile(
        primary_interests=["a", "b"], aesthetic_vibe="v", recommended_genres=["g"]
    )
    client = _FakeClient(parse_result=profile)
    out = await parse_json(
        client, model="m", system="s", user="u", output_model=InterestProfile
    )
    assert out is profile
    assert client.messages.parse_calls == 1


async def test_run_tool_loop_drives_tools_then_finishes():
    script = [
        _resp_tool_use([_tool_use_block("check_availability", {"title": "Black Mirror"})]),
        _resp_end_turn("all checked"),
    ]
    client = _FakeClient(create_script=script)
    calls: list = []

    async def executor(name, tool_input):
        calls.append((name, tool_input))
        raw = {"title": tool_input["title"], "found": True, "platforms": ["netflix"]}
        return "ok", raw

    text, captured = await run_tool_loop(
        client, model="m", system="s", user="u",
        tools=[{"name": "check_availability", "description": "", "input_schema": {}}],
        executor=executor,
    )
    assert text == "all checked"
    assert calls == [("check_availability", {"title": "Black Mirror"})]
    assert captured == [{"title": "Black Mirror", "found": True, "platforms": ["netflix"]}]
    assert client.messages.create_calls == 2


# ── RealProvider (analytical agents) ─────────────────────────
async def test_real_provider_profiles_via_parse(monkeypatch):
    profile = InterestProfile(
        primary_interests=["film"], aesthetic_vibe="arthouse", recommended_genres=["drama"]
    )
    fake = _FakeClient(parse_result=profile)
    monkeypatch.setattr(provider_mod, "build_async_client", lambda _s: fake)
    provider = RealProvider(get_settings())
    out = await provider.profile_interests(ProfileDump(handle="@x", bio="b"))
    assert out is profile


async def test_real_provider_match_drops_off_limits(monkeypatch):
    match = ShowMatch(picks=[
        ShowCandidate(title="Fleabag", why="x"),
        ShowCandidate(title="Black Mirror", why="y"),
    ])
    fake = _FakeClient(parse_result=match)
    monkeypatch.setattr(provider_mod, "build_async_client", lambda _s: fake)
    provider = RealProvider(get_settings())
    picks = await provider.match_shows(
        InterestProfile(primary_interests=["a"], aesthetic_vibe="v", recommended_genres=["g"]),
        handle="@x", off_limits=["Fleabag"], attempt=1,
    )
    assert [p.title for p in picks] == ["Black Mirror"]  # banned title removed


# ── Streaming Checker real-mode path (fake LLM + REAL MCP server) ──
async def test_streaming_checker_real_mode_uses_tool_loop_and_mcp(monkeypatch):
    real_settings = get_settings().model_copy(update={"app_mode": RunMode.REAL})
    # Model calls the tool for one title; the checker's backfill covers the rest.
    script = [
        _resp_tool_use([_tool_use_block("check_availability", {"title": "Fleabag"})]),
        _resp_end_turn("done"),
    ]
    monkeypatch.setattr(sc_mod, "build_async_client", lambda _s: _FakeClient(create_script=script))

    candidates = [
        ShowCandidate(title="Fleabag", why="prime only"),
        ShowCandidate(title="The White Lotus", why="hbo"),
    ]
    results = await check_availability(candidates, real_settings)
    by_title = {r.title: r for r in results}

    # Ground truth comes from the REAL MCP server, not the model's prose.
    assert by_title["Fleabag"].available is False  # prime-only
    assert by_title["The White Lotus"].available is True
    assert by_title["The White Lotus"].platforms == ["hbo"]
