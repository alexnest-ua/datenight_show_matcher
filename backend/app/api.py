"""FastAPI surface over the shared orchestrator.

The web UI consumes the SSE stream; everything is the SAME core the CLI uses
(``app.graph.pipeline``), so there is exactly one pipeline implementation.

Endpoints (see docs/contracts.md):
    GET  /health  ·  /api/health       liveness + resolved mode
    GET  /api/profiles                 known demo handles for the picker
    GET  /api/stream?handle=@x         SSE stream of PipelineEvents
    POST /api/run   {"handle": "@x"}   one-shot, non-streaming RunResult
"""

from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, StringConstraints
from sse_starlette.sse import EventSourceResponse

from app import __version__
from app.config import get_settings
from app.graph.pipeline import run_pipeline, run_pipeline_to_result
from app.mock_data.profiles import PROFILES
from app.models import EventType, RunResult

app = FastAPI(title="DateNight Show Matcher", version=__version__)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_TERMINAL = {EventType.RUN_COMPLETED, EventType.RUN_FAILED}

# Instagram-style handle: optional @, then 1-30 of [A-Za-z0-9._]. Bounding the
# input stops an unauthenticated request from driving unbounded pipeline work
# (the one hardening gap flagged in the security review).
_HANDLE_PATTERN = r"^@?[A-Za-z0-9._]{1,30}$"
Handle = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=1, max_length=64, pattern=_HANDLE_PATTERN
    ),
]


class RunRequest(BaseModel):
    handle: Handle


def _health_payload() -> dict:
    s = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "mode": s.effective_mode.value,
        "model_analysis": s.model_analysis,
        "model_fast": s.model_fast,
        "user_platforms": s.user_platforms,
    }


@app.get("/health")
@app.get("/api/health")
async def health() -> dict:
    return _health_payload()


@app.get("/api/profiles")
async def profiles() -> list[dict]:
    return [{"handle": p.handle, "display_name": p.display_name} for p in PROFILES.values()]


@app.get("/api/stream")
async def stream(
    request: Request,
    handle: Annotated[str, Query(min_length=1, max_length=64, pattern=_HANDLE_PATTERN)],
) -> EventSourceResponse:
    settings = get_settings()

    async def event_source():
        async for ev in run_pipeline(handle, settings):
            if await request.is_disconnected():
                break
            yield {"data": ev.model_dump_json(), "id": str(ev.seq)}
            if ev.event in _TERMINAL:
                break

    return EventSourceResponse(event_source())


@app.post("/api/run")
async def run(body: RunRequest) -> RunResult:
    return await run_pipeline_to_result(body.handle, get_settings())


@app.get("/")
async def root() -> dict:
    return {
        "name": "DateNight Show Matcher",
        "docs": "/docs",
        "endpoints": ["/health", "/api/profiles", "/api/stream?handle=@art_girl", "/api/run"],
        **_health_payload(),
    }
