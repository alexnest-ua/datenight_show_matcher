"""Streaming catalog access.

`catalog.json` is the source of truth. We seed a small SQLite database from it so
the MCP server queries a real "local DB" (as the assignment suggests), while the
rest of the app can also do fast in-memory lookups for enrichment.
"""

from __future__ import annotations

import json
import sqlite3
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

from app.config import get_settings


class CatalogEntry(BaseModel):
    title: str
    year: int | None = None
    genres: list[str] = []
    platforms: list[str] = []


def _catalog_path() -> Path:
    return get_settings().catalog_path


@lru_cache
def load_catalog() -> list[CatalogEntry]:
    raw = json.loads(_catalog_path().read_text(encoding="utf-8"))
    shows = raw["shows"] if isinstance(raw, dict) else raw
    return [CatalogEntry(**s) for s in shows]


@lru_cache
def _by_title() -> dict[str, CatalogEntry]:
    return {e.title.strip().lower(): e for e in load_catalog()}


def lookup(title: str) -> CatalogEntry | None:
    """Fast in-memory, case-insensitive lookup (used for enrichment)."""
    return _by_title().get(title.strip().lower())


# ─────────────────────────────────────────────────────────────
# SQLite (what the MCP server queries)
# ─────────────────────────────────────────────────────────────


def seed_sqlite(db_path: Path | None = None, *, force: bool = False) -> Path:
    """(Re)build the SQLite catalog from catalog.json. Idempotent."""
    path = db_path or get_settings().sqlite_path
    path.parent.mkdir(parents=True, exist_ok=True)
    if force and path.exists():
        path.unlink()

    con = sqlite3.connect(path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS shows (
                title     TEXT PRIMARY KEY COLLATE NOCASE,
                year      INTEGER,
                genres    TEXT NOT NULL,   -- JSON array
                platforms TEXT NOT NULL    -- JSON array
            )
            """
        )
        rows = [
            (e.title, e.year, json.dumps(e.genres), json.dumps(e.platforms))
            for e in load_catalog()
        ]
        con.executemany(
            "INSERT OR REPLACE INTO shows (title, year, genres, platforms) "
            "VALUES (?, ?, ?, ?)",
            rows,
        )
        con.commit()
    finally:
        con.close()
    return path


def ensure_seeded(db_path: Path | None = None) -> Path:
    """Seed the DB only if it doesn't exist yet."""
    path = db_path or get_settings().sqlite_path
    if not path.exists():
        seed_sqlite(path)
    return path


def query_sqlite(title: str, db_path: Path | None = None) -> CatalogEntry | None:
    """Case-insensitive title lookup against the SQLite catalog (used by MCP)."""
    path = ensure_seeded(db_path)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(
            "SELECT title, year, genres, platforms FROM shows "
            "WHERE title = ? COLLATE NOCASE",
            (title.strip(),),
        ).fetchone()
    finally:
        con.close()
    if row is None:
        return None
    return CatalogEntry(
        title=row["title"],
        year=row["year"],
        genres=json.loads(row["genres"]),
        platforms=json.loads(row["platforms"]),
    )
