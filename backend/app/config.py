"""Centralised, env-driven configuration (pydantic-settings).

The whole app is configured from environment variables / a local `.env`.
It is designed to run with ZERO configuration in offline mock mode, so the
demo and the test-suite work without an API key or any network access.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> backend/app -> backend -> <repo root>
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
REPO_ROOT = BACKEND_DIR.parent


class RunMode(StrEnum):
    """How the LLM layer resolves at runtime."""

    AUTO = "auto"
    REAL = "real"
    MOCK = "mock"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Credentials & mode ───────────────────────────────────
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    app_mode: RunMode = Field(default=RunMode.AUTO, alias="APP_MODE")

    # ── Models (analytical "Sonnet" tier vs fast "Haiku" tier) ─
    model_analysis: str = Field(default="claude-sonnet-4-6", alias="MODEL_ANALYSIS")
    model_fast: str = Field(default="claude-haiku-4-5-20251001", alias="MODEL_FAST")
    insta_reader_use_llm: bool = Field(default=False, alias="INSTA_READER_USE_LLM")

    # ── Pipeline behaviour ───────────────────────────────────
    max_repicks: int = Field(default=3, ge=0, le=10, alias="MAX_REPICKS")
    user_platforms: list[str] = Field(default=["netflix", "hbo"], alias="USER_PLATFORMS")

    # ── HTTP / API ───────────────────────────────────────────
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8090, alias="API_PORT")
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
        ],
        alias="CORS_ORIGINS",
    )

    # ── Misc ─────────────────────────────────────────────────
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    request_timeout: float = Field(default=60.0, alias="REQUEST_TIMEOUT")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")

    @field_validator("user_platforms", "cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        """Accept comma-separated strings from env (e.g. "netflix,hbo")."""
        if isinstance(value, str):
            return [item.strip().lower() for item in value.split(",") if item.strip()]
        return value

    @property
    def has_api_key(self) -> bool:
        return bool(self.anthropic_api_key and self.anthropic_api_key.strip())

    @property
    def effective_mode(self) -> RunMode:
        """Resolve AUTO -> REAL/MOCK based on key presence."""
        if self.app_mode is RunMode.AUTO:
            return RunMode.REAL if self.has_api_key else RunMode.MOCK
        return self.app_mode

    @property
    def is_mock(self) -> bool:
        return self.effective_mode is RunMode.MOCK

    @property
    def catalog_path(self) -> Path:
        return APP_DIR / "data" / "catalog.json"

    @property
    def sqlite_path(self) -> Path:
        """On-disk SQLite the MCP server queries (seeded from catalog.json)."""
        return APP_DIR / "data" / "catalog.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
