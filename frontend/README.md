# DateNight Show Matcher — Frontend

A polished single-page demo UI for **PlayFix · DateNight Show Matcher**. It
visualises a 4-stage Claude agent pipeline (`insta_reader → interest_profiler →
show_matcher → streaming_checker`, with a re-pick loop) that profiles an
Instagram handle and recommends three date-night TV shows available on the
user's streaming subscriptions (Netflix + HBO).

Built with **React 19 + Vite 8 + TypeScript** (strict). External CSS only,
flexbox layout, CSS custom properties for theming, WCAG 2.1 AA.

## Dual mode (auto-detected on startup)

The app works with **or without** a backend and silently picks the right mode —
it never shows a broken or blank state.

- **LIVE** — On startup it probes `GET ${VITE_API_BASE}/health` (1.5s timeout).
  If it returns `{status:"ok"}`, the app runs the real pipeline over SSE
  (`GET /api/stream?handle=…`) and loads the picker from `GET /api/profiles`. A
  green **LIVE** pill is shown.
- **DEMO** — If no backend is reachable, the app replays a bundled recorded run
  from `src/demo/*.json` (scheduled by each event's `elapsed_ms`, lightly
  time-compressed to ~6–10s). An amber **DEMO** pill is shown. The picker lists
  the handles found in the bundled fixtures.

Force a mode:

- `?demo=1` in the URL → always DEMO.
- Set `VITE_API_BASE` and ensure `/health` passes → LIVE is preferred.

## Scripts

```bash
# install (use bun — no global node/npm in this environment)
~/.bun/bin/bun install

# dev server (http://localhost:5173). With an empty VITE_API_BASE it proxies
# /api and /health to http://localhost:8090, so no CORS setup is needed.
~/.bun/bin/bun run dev

# type-check only
~/.bun/bin/bun run typecheck

# production build → dist/  (runs tsc --noEmit then vite build)
~/.bun/bin/bun run build

# preview the production build locally
~/.bun/bin/bun run preview
```

## Environment

| Var             | Default | Purpose                                                            |
| --------------- | ------- | ------------------------------------------------------------------ |
| `VITE_API_BASE` | `""`    | Backend origin. Empty = same-origin (dev proxy) / DEMO fallback.   |

Copy `.env.example` to `.env` to override locally.

## Demo fixtures

`src/demo/*.json` matches the recorded-run format in `docs/contracts.md` §5:

```jsonc
{ "username": "@art_girl", "mode": "mock", "events": [ /* PipelineEvent[] */ ] }
```

One placeholder fixture (`art_girl.json`, including a re-pick) ships so the app
runs immediately. The glob loader (`import.meta.glob('./demo/*.json')`) picks up
**any** fixtures dropped into `src/demo/` later — handle lists are derived from
the files, never hardcoded. Generate more with `datenight demo-fixtures` from
the backend.

## Cloudflare Pages

| Setting          | Value          |
| ---------------- | -------------- |
| Build command    | `bun run build`|
| Build output dir | `dist`         |
| Env var          | leave `VITE_API_BASE` unset → app runs in **DEMO** mode automatically |

`public/_redirects` (`/*  /index.html  200`) provides the SPA routing fallback.
To point the deployed site at a live backend instead, set `VITE_API_BASE` to its
origin in the Pages project settings.
```
