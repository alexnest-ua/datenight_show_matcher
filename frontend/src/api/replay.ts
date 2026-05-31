/**
 * DEMO-mode replay engine. Loads every bundled recorded run from src/demo/*.json
 * and replays an event stream by scheduling each event at its `elapsed_ms`
 * (time-compressed for snappiness, then clamped to a ~6–10s total). This
 * reproduces the live staged experience with zero backend.
 */
import type {
  PipelineEvent,
  ProfileSummary,
  RecordedRun,
} from "../types.ts";

// Eagerly bundle all fixtures. Whatever files exist under src/demo/ get picked
// up — no hardcoded handle list. The backend can drop more fixtures in later.
const modules = import.meta.glob<RecordedRun>("../demo/*.json", {
  eager: true,
  import: "default",
});

/** Normalise a handle for keying (strip leading @, lowercase). */
function normalise(handle: string): string {
  return handle.trim().replace(/^@+/, "").toLowerCase();
}

/** All loaded fixtures, keyed by normalised handle. */
const fixtures = new Map<string, RecordedRun>();
for (const run of Object.values(modules)) {
  if (run && Array.isArray(run.events) && typeof run.username === "string") {
    fixtures.set(normalise(run.username), run);
  }
}

/**
 * Derive the picker list from loaded fixtures. display_name is pulled from the
 * run_started message / the insta_reader stage output when available, else the
 * handle is used.
 */
export function demoProfiles(): ProfileSummary[] {
  const out: ProfileSummary[] = [];
  for (const run of fixtures.values()) {
    out.push({
      handle: run.username,
      display_name: displayNameFor(run),
    });
  }
  return out.sort((a, b) => a.handle.localeCompare(b.handle));
}

function displayNameFor(run: RecordedRun): string {
  // The insta_reader stage_completed payload carries display_name.
  for (const ev of run.events) {
    if (ev.event === "stage_completed" && ev.stage === "insta_reader") {
      const data = ev.data as { display_name?: string } | null;
      if (data?.display_name) return data.display_name;
    }
  }
  return run.username;
}

/** Does a fixture exist for this handle? */
export function hasFixture(handle: string): boolean {
  return fixtures.has(normalise(handle));
}

/** Get the fixture for a handle, falling back to the first one available. */
export function fixtureFor(handle: string): RecordedRun | null {
  const key = normalise(handle);
  if (fixtures.has(key)) return fixtures.get(key) ?? null;
  // Fall back to any fixture so the demo never dead-ends on an unknown handle.
  const first = fixtures.values().next();
  return first.done ? null : first.value;
}

// Replay timing knobs.
const SPEED_FACTOR = 0.7; // <1 compresses time (snappier)
const MIN_TOTAL_MS = 6000;
const MAX_TOTAL_MS = 10000;

export interface ReplayHandlers {
  onEvent: (event: PipelineEvent) => void;
  onError: (message: string) => void;
}

/**
 * Replay a recorded run. Returns a canceller that clears all pending timers
 * (call on unmount / new run). Safe to call the canceller multiple times.
 */
export function replayRun(handle: string, handlers: ReplayHandlers): () => void {
  const run = fixtureFor(handle);
  if (!run || run.events.length === 0) {
    handlers.onError("No demo recording is available for this profile.");
    return () => {};
  }

  // Determine the scaling so the whole run lands in the clamp window.
  const rawMax = run.events.reduce(
    (max, ev) => Math.max(max, ev.elapsed_ms ?? 0),
    0,
  );
  const compressed = rawMax * SPEED_FACTOR;
  const clampedTotal = Math.min(
    MAX_TOTAL_MS,
    Math.max(MIN_TOTAL_MS, compressed),
  );
  // Scale every timestamp uniformly to hit clampedTotal (preserves the staged
  // rhythm). Guard against a zero-length run.
  const scale = rawMax > 0 ? clampedTotal / rawMax : 0;

  const timers: ReturnType<typeof setTimeout>[] = [];
  let cancelled = false;

  for (const ev of run.events) {
    const delay = Math.round((ev.elapsed_ms ?? 0) * scale);
    const t = setTimeout(() => {
      if (cancelled) return;
      handlers.onEvent(ev);
    }, delay);
    timers.push(t);
  }

  return () => {
    if (cancelled) return;
    cancelled = true;
    for (const t of timers) clearTimeout(t);
  };
}
