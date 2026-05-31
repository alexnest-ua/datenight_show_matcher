"""Local MCP server exposing streaming availability.

A real Model Context Protocol server (stdio transport) with a single tool,
``check_availability``, backed by the SQLite catalog. The Streaming Checker agent
connects to this over stdio and lets Claude call the tool (function calling).

Run standalone:  python -m app.mcp_server.server
Inspect:         mcp dev app/mcp_server/server.py     (requires `mcp[cli]`)

IMPORTANT (stdio rule): never write to stdout here — it corrupts the JSON-RPC
stream. FastMCP handles framing; logging goes to stderr only.
"""

from __future__ import annotations

import sys

from mcp.server.fastmcp import FastMCP

from app.data_access.catalog import ensure_seeded, query_sqlite

# Quiet INFO chatter on stderr so it doesn't clutter the CLI live view / recordings.
mcp = FastMCP("datenight-streaming", log_level="WARNING")


@mcp.tool()
def check_availability(title: str) -> dict:
    """Look up which streaming platforms carry a TV series.

    Queries the local catalog database and returns every platform the title is
    available on (e.g. "netflix", "hbo", "prime"). The caller is responsible for
    filtering to the user's own subscriptions.

    Args:
        title: The series title (case-insensitive, exact match).

    Returns:
        {"title", "found", "platforms": [...], "year", "genres": [...]}
    """
    entry = query_sqlite(title)
    if entry is None:
        return {"title": title, "found": False, "platforms": [], "year": None, "genres": []}
    return {
        "title": entry.title,
        "found": True,
        "platforms": entry.platforms,
        "year": entry.year,
        "genres": entry.genres,
    }


def main() -> None:
    # Make sure the DB exists before we start serving (logs to stderr, not stdout).
    print("[mcp] seeding catalog DB…", file=sys.stderr)
    ensure_seeded()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
