# Architecture

How DateNight Show Matcher is built. For *running* it see the [README](../README.md);
for the exact wire types see [contracts.md](contracts.md).

## The core idea: one brain, two surfaces

`backend/app/graph/pipeline.py::run_pipeline()` is the entire orchestration. The **CLI**
and the **FastAPI/SSE** endpoint are just two renderers of the same `PipelineEvent` stream,
so they can never drift. The web demo replays *recorded* versions of that same stream.

## Components

```mermaid
flowchart TB
    WEB["React SPA (Vite)<br/>dual-mode: live SSE ↔ recorded replay"]

    subgraph Surfaces["Surfaces (thin)"]
        CLI["CLI · Typer/Rich<br/>get-show @username"]
        API["FastAPI · SSE<br/>/api/stream · /api/run · /health"]
    end

    subgraph Core["Core (shared)"]
        ORCH["Orchestrator<br/>LangGraph StateGraph"]
        subgraph AG["Sub-agents"]
            A1["#1 Insta Reader"]
            A2["#2 Interest Profiler"]
            A3["#3 Show Matcher"]
            A4["#4 Streaming Checker"]
        end
        PROV["LLMProvider<br/>RealProvider ↔ MockProvider"]
    end

    subgraph EXT["External / data"]
        ANTH["Anthropic Messages API"]
        MCP["MCP stdio server<br/>tool: check_availability"]
        DB[("SQLite catalog<br/>seeded from catalog.json")]
    end

    WEB -->|"SSE / replay"| API
    CLI --> ORCH
    API --> ORCH
    ORCH --> A1 --> A2 --> A3 --> A4
    A4 -. "re-pick (capped)" .-> A3
    A2 --> PROV
    A3 --> PROV
    PROV -->|"real mode"| ANTH
    A4 -->|"tool-use loop"| MCP --> DB
```

- **Surfaces are thin.** They translate input → `run_pipeline(handle)` and render the event stream.
- **Agents talk to an `LLMProvider`**, not to the SDK directly — so the same graph runs against the
  real API or a deterministic mock. Only the LLM is swapped; the MCP server + SQLite run in **both** modes.
- **The Streaming Checker** is the function-calling showcase: it drives the MCP `check_availability`
  tool. Availability is then computed **in code** from the tool's return — never trusted to the model.

## A run, step by step

```mermaid
sequenceDiagram
    actor U as User
    participant O as Orchestrator
    participant S as Sonnet (Profiler/Matcher)
    participant H as Haiku (Checker)
    participant M as MCP + SQLite

    U->>O: get-show @art_girl
    O->>O: #1 Insta Reader → profile dump (mock)
    O->>S: #2 Interest Profiler
    S-->>O: InterestProfile (strict JSON)
    O->>S: #3 Show Matcher (attempt 1)
    S-->>O: Fleabag, The White Lotus, Normal People
    O->>H: #4 Streaming Checker
    H->>M: check_availability("Fleabag")
    M-->>H: { platforms: ["prime"] }
    Note over O,H: Fleabag not on Netflix/HBO → exclude → re-pick
    O->>S: #3 Show Matcher (attempt 2, off-limits: Fleabag)
    S-->>O: Sex Education, ...
    O->>H: #4 Streaming Checker
    H->>M: check_availability("Sex Education")
    M-->>H: { platforms: ["netflix"] }
    O-->>U: The White Lotus·HBO · Normal People·HBO · Sex Education·Netflix
```

The conditional **re-pick loop** is why this is a `StateGraph` and not three `await`s: the
checker's edge routes back to the matcher (passing excluded titles as off-limits), bounded by
`MAX_REPICKS` + LangGraph's `recursion_limit`. Picks accumulate across attempts; if it can't fill
three on the user's subscriptions it ends gracefully with 0–3.

## Pipeline state machine

```mermaid
stateDiagram-v2
    [*] --> insta_reader
    insta_reader --> interest_profiler
    interest_profiler --> show_matcher
    show_matcher --> streaming_checker
    streaming_checker --> show_matcher: repick (need more & attempts < cap)
    streaming_checker --> [*]: done (3 on subs)
    streaming_checker --> [*]: give_up (cap reached)
```

## Data contracts

Typed pydantic models flow between nodes (source of truth: `backend/app/models.py`, mirrored in
`frontend/src/types.ts` and documented in [contracts.md](contracts.md)):

`ProfileDump` → `InterestProfile` → `ShowCandidate[]` → `Availability[]` → `RunResult`, with a
`PipelineEvent` envelope (`seq`, `elapsed_ms`, `stage`, `event`, `data`) streamed over SSE and
stored verbatim in the demo fixtures.

## Real vs. mock

`APP_MODE=auto` (default) → **real** when `ANTHROPIC_API_KEY` is set, else **mock**.

| | Real | Mock |
|---|---|---|
| Profiler / Matcher | Anthropic `messages.parse` (schema-validated JSON) | scripted fixtures per handle |
| Streaming Checker | Anthropic tool-use loop → MCP | direct MCP call (no LLM) |
| MCP server + SQLite | ✅ used | ✅ used |
| Model tiers | Sonnet (analysis) · Haiku (fast) | — |

## Why these choices

- **Orchestrator + sub-agents** — separation of concerns and cost control (Haiku for routine
  parse/checks, Sonnet for analysis), exactly as the brief frames it.
- **LangGraph** — an explicit, inspectable state machine with a *conditional loop* and built-in
  streaming; maps cleanly onto CrewAI / n8n if needed.
- **A real MCP server** — isolates the external-availability boundary behind a tool the model calls
  (genuine function calling), the pattern the role centres on. The Anthropic MCP *connector* only
  speaks to remote HTTPS servers, so a local **stdio** server uses a manual client→tool bridge.
- **Structured outputs** (`messages.parse` + pydantic) — guaranteed-valid JSON, no fragile parsing.
- **Ground-truth in code** — the user-subscription filter (Netflix/HBO; Prime ignored) is applied
  to the MCP tool's data, so a hallucinated title simply comes back unavailable and is re-picked.
- **Dual-mode frontend** — deploys to Cloudflare Pages with no backend (replays bundled runs) or
  streams live SSE locally; same event contract either way.

## Tech stack

Python 3.12 · LangGraph 1.2 · MCP SDK 1.27 · Anthropic SDK 0.105 · FastAPI 0.136 + sse-starlette ·
Typer/Rich · pydantic v2. Frontend: React 19 · Vite 8 · TypeScript. Packaging: Docker Compose
(uvicorn backend + nginx web), 24 pytest tests, ruff.
