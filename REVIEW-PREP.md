# Code-Review Prep — DateNight Show Matcher

> Companion to [docs/architecture.md](docs/architecture.md): design rationale + an
> anticipated-questions FAQ for walking through the codebase.

## 30-second pitch
One command (`get-show @username`) runs a **Claude orchestrator + 4 sub-agents** that
profile an Instagram handle and recommend **3 date-night shows you can actually stream
on Netflix/HBO**. It runs against the **real Claude API** or a **deterministic offline mock**,
checks availability through a **real MCP tool over SQLite**, and re-picks anything not on
the user's subscriptions. The CLI is the spec deliverable; a React web UI is layered on the
same core.

## The assignment → how it maps
| Brief role | File | Model tier | What it does |
|---|---|---|---|
| Orchestrator | `app/graph/pipeline.py` | — | LangGraph `StateGraph`, passes JSON state, runs the re-pick loop, streams events |
| #1 Insta Reader | `app/agents/insta_reader.py` | Haiku/mock | returns a pre-baked profile dump (no scraping, per the FAQ) |
| #2 Interest Profiler | `app/agents/interest_profiler.py` | Sonnet | raw text → strict-JSON `InterestProfile` |
| #3 Show Matcher | `app/agents/show_matcher.py` | Sonnet | profile → ranked top-3 with reasoning |
| #4 Streaming Checker | `app/agents/streaming_checker.py` | Haiku + **MCP** | tool-use loop calling `check_availability`; filters to Netflix/HBO |

## Request lifecycle
```
get-show @art_girl  (CLI)         POST /api/run · GET /api/stream (web, SSE)
        └──────────────┬───────────────────┘
                 run_pipeline()  (app/graph/pipeline.py)  ← ONE core, two surfaces
                       │  emits PipelineEvent stream (seq, elapsed_ms, stage, data)
   START → insta_reader → interest_profiler → show_matcher → streaming_checker
                                                  ↑                  │ check_availability
                                                  └─── repick ───────┤   ↓ (stdio)
                                          (capped: MAX_REPICKS)      │  MCP server → SQLite
                                                       done/give_up →┴→ END → RunResult
```
- Each node emits progress via `get_stream_writer`; the orchestrator stamps `seq`+`elapsed_ms`
  and yields typed `PipelineEvent`s. CLI prints them (Rich); API relays over SSE; the demo
  fixtures are recorded versions of the same stream.

## File map
- `app/config.py` — pydantic-settings: `APP_MODE` (auto/real/mock), model IDs, `USER_PLATFORMS`, CORS, ports.
- `app/models.py` — the contracts (also mirrored in `frontend/src/types.ts` and `docs/contracts.md`).
- `app/llm/anthropic_client.py` — `parse_json` (structured output) + `run_tool_loop` (manual tool-use) + prompt-cache wiring.
- `app/llm/provider.py` — `LLMProvider` ABC → `RealProvider` (Anthropic) / `MockProvider` (fixtures); `build_provider()`.
- `app/mcp_server/server.py` — FastMCP **stdio** server, tool `check_availability(title)`.
- `app/mcp_server/client.py` — stdio client bridge (MCP `inputSchema` → Anthropic `input_schema`).
- `app/data_access/catalog.py` — `catalog.json` → SQLite seed + lookups.
- `app/mock_data/{profiles,fixtures}.py` — IG dumps + scripted analytical outputs per handle.
- `app/cli.py` (Typer/Rich) · `app/api.py` (FastAPI/SSE) — the two surfaces over the core.
- `frontend/src/` — React; `useMode` (LIVE↔DEMO), `usePipeline`, `api/client.ts` (EventSource), `api/replay.ts`, `lib/events.ts`.

## Key design decisions (defend these)
1. **Orchestrator + sub-agents** → separation of concerns + **cost control**: cheap Haiku on
   routine parse/check, Sonnet on analysis (exactly what the brief asks).
2. **LangGraph** over a hand-rolled loop → explicit, inspectable state machine with a *conditional
   loop* (the re-pick) and built-in streaming; trivial to add nodes. (Maps cleanly to CrewAI/n8n;
   I chose LangGraph for the transparent graph + the loop edge.)
3. **Real MCP server** (not a fake function) → the role emphasizes MCP + function calling. It
   isolates the "external availability data" boundary behind a tool the model calls.
4. **Strict JSON via `client.messages.parse(output_format=PydanticModel)`** → schema-validated
   output, no brittle regex / `json.loads` of free text.
5. **Availability is ground-truthed in code**, not from the model's prose: the checker computes
   `available = platforms ∩ user_subs` from the **MCP tool's return**. The LLM only *drives* the
   tool calls (function-calling demo); it can't lie about availability.
6. **Dual provider (real/mock)** → the whole pipeline runs offline, deterministic, key-free
   (demo, tests, CI). Only the LLM is mocked; the MCP server + SQLite run in **both** modes.
7. **Dual-mode frontend** → works on Cloudflare Pages with **no backend** (replays bundled
   recorded runs) or live SSE locally. Auto-detects via a `/health` probe.

## Function calling + MCP (the hot button)
- `app/mcp_server/server.py` is a genuine MCP stdio server (`FastMCP`, tool returns a dict →
  structured output). `client.py` spawns it, lists tools, and maps the schema into Anthropic's
  `tools=[...]`. In **real** mode the checker runs `run_tool_loop`: `messages.create(tools=…)` →
  on `stop_reason=="tool_use"` execute the tool against MCP → return `tool_result` → repeat until
  `end_turn`. We also **backfill** any title the model didn't check, so coverage is guaranteed.
- Why not Anthropic's MCP *connector*? It only supports remote HTTPS servers; for a **local stdio**
  server the manual bridge is the correct (and only) pattern.

## How correctness is guaranteed
- **Valid JSON:** structured outputs (schema-enforced) for Profiler/Matcher.
- **No infinite loop:** re-pick bounded by `MAX_REPICKS` (state counter) + LangGraph `recursion_limit`;
  picks accumulate across attempts; if it can't fill 3, it ends gracefully with 0–3 (UI shows an
  empty-state message).
- **Off-limits:** excluded + already-accepted titles are passed back as `off_limits` so the matcher
  never re-suggests them; `_drop_off_limits` defends even if the model ignores that.

## Security (already reviewed clean)
- `handle` validated at the API boundary (`^@?[A-Za-z0-9._]{1,30}$`, max 64) → no unbounded work.
- SQLite fully parameterized; subprocess spawned with **fixed** args (no shell, no user input).
- `ANTHROPIC_API_KEY` never logged/echoed/returned; `.env` + creds + the PDF gitignored.
- CORS is an explicit allow-list (not `*`); React auto-escapes all rendered strings (no XSS).

## Testing
24 pytest tests, ruff clean: catalog/SQLite, mock provider, **real MCP tool + checker** (integration),
the **re-pick loop** end-to-end, FastAPI + SSE, and the **real-mode code paths via a stubbed Anthropic
client** (so `parse_json`/`run_tool_loop`/`RealProvider` are exercised with no key). Frontend: `tsc` + build.

## What's mocked / honest production gaps
- Mock Instagram dumps + mock streaming catalog (by design, per the brief).
- No auth/rate-limiting beyond input validation; single-process; MCP spawned per checker call.
- Real-API path is verified via a **stubbed SDK**, not yet against the live API (needs a key).
- For production I'd: swap the MCP tool's SQLite for a real availability API (same interface), add
  CI + observability + retries/backoff, persist runs, and add auth/rate-limits.

## Likely reviewer questions → crisp answers
- *"Why LangGraph and not just three awaits?"* → I need a **conditional loop** (re-pick) + streamed
  progress + an inspectable graph; LangGraph gives that with little code and is swappable for CrewAI/n8n.
- *"What if the model invents a show?"* → the Checker queries the **catalog via MCP**; unknown titles
  come back `found:false` → unavailable → re-pick. Availability never trusts the model.
- *"How do you keep it cheap?"* → Haiku for parse/check, Sonnet for analysis; prompt caching wired;
  mock mode for dev/CI.
- *"Why is `messages.parse` better than asking for JSON?"* → schema validation at the API layer; the
  SDK retries on mismatch; no fragile parsing.
- *"The PDF's model IDs?"* → `claude-3-5-*-20241022` were retired (Oct-25/Feb-26 → 404); I default to
  `claude-sonnet-4-6` / `claude-haiku-4-5`, configurable via env. (Good signal that I checked.)
- *"How does the web demo work with a localhost backend?"* → dual-mode: CF Pages replays recorded
  runs (no backend); locally it streams live SSE. Same event contract.

## Quick demo script
```bash
make cli HANDLE=@art_girl     # CLI: re-pick demo (Fleabag→prime→re-pick→Sex Education)
make cli HANDLE=@fitness_jane # CLI: clean happy path (1 attempt)
docker compose up             # web :8091 (LIVE) + backend :8090; or open the pages.dev demo link
make test                     # 24 tests, no key needed
```
