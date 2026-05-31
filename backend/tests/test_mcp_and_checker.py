"""Integration: the real stdio MCP server + the Streaming Checker over it."""

from app.agents.streaming_checker import check_availability
from app.config import get_settings
from app.mcp_server.client import MCPCatalogClient
from app.models import ShowCandidate


async def test_mcp_tool_round_trip():
    async with MCPCatalogClient(get_settings()) as mcp:
        tools = mcp.anthropic_tools()
        assert any(t["name"] == "check_availability" for t in tools)
        # bridged schema shape Anthropic expects
        tool = next(t for t in tools if t["name"] == "check_availability")
        assert "input_schema" in tool

        found = await mcp.check("Fleabag")
        assert found["found"] is True and "prime" in found["platforms"]

        missing = await mcp.check("Definitely Not A Real Show")
        assert missing["found"] is False
        assert missing["platforms"] == []


async def test_checker_filters_to_subscriptions():
    candidates = [
        ShowCandidate(title="Fleabag", why="prime only"),
        ShowCandidate(title="The White Lotus", why="on hbo"),
        ShowCandidate(title="Black Mirror", why="on netflix"),
    ]
    results = await check_availability(candidates, get_settings())
    by_title = {r.title: r for r in results}

    # Prime-only -> not available on the user's subscriptions.
    assert by_title["Fleabag"].found is True
    assert by_title["Fleabag"].available is False
    assert by_title["Fleabag"].platforms == []

    # HBO / Netflix -> available, filtered to the user's subs.
    assert by_title["The White Lotus"].available is True
    assert by_title["The White Lotus"].platforms == ["hbo"]
    assert by_title["Black Mirror"].available is True
    assert by_title["Black Mirror"].platforms == ["netflix"]
