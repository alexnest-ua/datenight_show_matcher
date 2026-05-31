"""Async client bridge for the local MCP server.

Spawns ``python -m app.mcp_server.server`` over stdio, lists its tools, and
exposes:
  * ``anthropic_tools()`` — the tool defs mapped into Anthropic's ``input_schema``
    shape (MCP uses camelCase ``inputSchema``; Anthropic uses ``input_schema``),
  * ``check(title)`` — call ``check_availability`` and return the structured JSON.

The Anthropic MCP *connector* only speaks to remote HTTPS servers, so for a local
stdio server this manual bridge is the correct pattern.
"""

from __future__ import annotations

import json
import os
import sys
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import BACKEND_DIR, Settings

TOOL_NAME = "check_availability"


class MCPCatalogClient:
    """Async context manager around a stdio MCP session."""

    def __init__(self, settings: Settings | None = None):
        self._settings = settings
        env = os.environ.copy()
        # Ensure the subprocess can import the `app` package regardless of cwd.
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{BACKEND_DIR}{os.pathsep}{existing}" if existing else str(BACKEND_DIR)
        )
        self._params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "app.mcp_server.server"],
            env=env,
            cwd=str(BACKEND_DIR),
        )
        self._stack = AsyncExitStack()
        self._session: ClientSession | None = None
        self._tools: list[Any] = []

    async def __aenter__(self) -> MCPCatalogClient:
        read, write = await self._stack.enter_async_context(stdio_client(self._params))
        self._session = await self._stack.enter_async_context(ClientSession(read, write))
        await self._session.initialize()
        listed = await self._session.list_tools()
        self._tools = list(listed.tools)
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self._stack.aclose()

    def anthropic_tools(self) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description or "",
                "input_schema": t.inputSchema,
            }
            for t in self._tools
        ]

    async def call(self, name: str, arguments: dict) -> dict:
        assert self._session is not None, "client not entered"
        result = await self._session.call_tool(name, arguments)
        structured = getattr(result, "structuredContent", None)
        if structured:
            # FastMCP wraps non-dict returns under {"result": ...}; ours is already a dict.
            if isinstance(structured, dict):
                return structured.get("result", structured)
            return structured
        for block in result.content:
            if getattr(block, "type", None) == "text":
                return json.loads(block.text)
        return {}

    async def check(self, title: str) -> dict:
        return await self.call(TOOL_NAME, {"title": title})
