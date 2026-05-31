"""Shared test fixtures.

Forces deterministic offline MOCK mode and zeroes the simulated per-stage delays
so the suite runs fast without any API key or network.
"""

from __future__ import annotations

import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    get_settings.cache_clear()

    import app.graph.pipeline as pipeline_mod

    monkeypatch.setattr(
        pipeline_mod, "MOCK_DELAYS", {k: 0.0 for k in pipeline_mod.MOCK_DELAYS}
    )
    yield
    get_settings.cache_clear()
