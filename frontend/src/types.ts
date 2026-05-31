/**
 * TypeScript mirror of the FROZEN wire contracts.
 *
 * Source of truth: backend/app/models.py + docs/contracts.md.
 * Keep these in lock-step with the Python pydantic models — the SSE stream and
 * the recorded-run demo fixtures both serialize exactly these shapes.
 */

// ─────────────────────────────────────────────────────────────
// Enums (string unions — match the Python str-Enum values verbatim)
// ─────────────────────────────────────────────────────────────

export type EventType =
  | "run_started"
  | "stage_started"
  | "stage_progress"
  | "stage_completed"
  | "stage_failed"
  | "repick"
  | "run_completed"
  | "run_failed";

export type Stage =
  | "insta_reader"
  | "interest_profiler"
  | "show_matcher"
  | "streaming_checker";

/** Canonical stage order (matches STAGE_ORDER in models.py). */
export const STAGE_ORDER: readonly Stage[] = [
  "insta_reader",
  "interest_profiler",
  "show_matcher",
  "streaming_checker",
];

/** Human-facing labels (matches STAGE_LABELS in models.py). */
export const STAGE_LABELS: Record<Stage, string> = {
  insta_reader: "Insta Reader",
  interest_profiler: "Interest Profiler",
  show_matcher: "Show Matcher",
  streaming_checker: "Streaming Checker",
};

// ─────────────────────────────────────────────────────────────
// Stage payloads (stage_completed.data — §3 of contracts.md)
// ─────────────────────────────────────────────────────────────

/** Stage 1 — insta_reader output. */
export interface ProfileDump {
  handle: string;
  display_name?: string;
  bio?: string;
  posts?: string[];
  hashtags?: string[];
}

/** Stage 2 — interest_profiler output (also RunResult.profile). */
export interface InterestProfile {
  primary_interests: string[];
  aesthetic_vibe: string;
  recommended_genres: string[];
}

/** A single show candidate from the matcher. */
export interface ShowCandidate {
  title: string;
  year?: number | null;
  genres: string[];
  why: string;
}

/** Stage 3 — show_matcher output. */
export interface ShowMatcherData {
  candidates: ShowCandidate[];
}

/** One availability lookup. */
export interface Availability {
  title: string;
  found: boolean;
  available: boolean;
  /** Subset of the user's subscriptions it streams on. */
  platforms: string[];
  /** Every platform it's on (incl. ones the user doesn't have). */
  all_platforms: string[];
}

/** Stage 4 — streaming_checker output. */
export interface StreamingCheckerData {
  results: Availability[];
}

// ─────────────────────────────────────────────────────────────
// Run-level payloads
// ─────────────────────────────────────────────────────────────

/** run_started.data */
export interface RunStartedData {
  username: string;
  mode: string;
  user_platforms: string[];
}

/** stage_progress.data (optional note) */
export interface StageProgressData {
  note?: string;
}

/** A title dropped for not being on the subs. */
export interface ExcludedShow {
  title: string;
  reason: string;
}

/** repick.data */
export interface RepickData {
  excluded: ExcludedShow[];
}

/** A final, ranked recommendation. */
export interface FinalPick {
  title: string;
  year?: number | null;
  genres: string[];
  why: string;
  /** User subscriptions it streams on, e.g. ["netflix"]. */
  platforms: string[];
}

/** run_completed.data — the full result (§2 of contracts.md). */
export interface RunResult {
  username: string;
  mode: string;
  profile: InterestProfile;
  picks: FinalPick[];
  excluded: ExcludedShow[];
  attempts: number;
  user_platforms: string[];
}

/** stage_failed.data / run_failed.data */
export interface ErrorData {
  error: string;
}

// ─────────────────────────────────────────────────────────────
// The streaming unit
// ─────────────────────────────────────────────────────────────

/**
 * One event emitted by the orchestrator. `data` is a permissive JSON value
 * keyed by `event`/`stage`; helpers in `lib/events.ts` narrow it safely.
 */
export interface PipelineEvent {
  seq: number;
  event: EventType;
  stage?: Stage | null;
  attempt?: number;
  elapsed_ms?: number;
  message?: string;
  data?: PipelineEventData;
}

/** Discriminated by `event` + `stage` at the call sites that read it. */
export type PipelineEventData =
  | RunStartedData
  | StageProgressData
  | ProfileDump
  | InterestProfile
  | ShowMatcherData
  | StreamingCheckerData
  | RepickData
  | RunResult
  | ErrorData
  | Record<string, unknown>
  | unknown[]
  | null;

// ─────────────────────────────────────────────────────────────
// HTTP surface (§4 of contracts.md)
// ─────────────────────────────────────────────────────────────

/** GET /health response. */
export interface HealthResponse {
  status: string;
  version?: string;
  mode?: string;
  model_analysis?: string;
  model_fast?: string;
  user_platforms?: string[];
}

/** One entry from GET /api/profiles. */
export interface ProfileSummary {
  handle: string;
  display_name: string;
}

// ─────────────────────────────────────────────────────────────
// Recorded-run demo fixture (§5 of contracts.md)
// ─────────────────────────────────────────────────────────────

export interface RecordedRun {
  username: string;
  mode: string;
  events: PipelineEvent[];
}

// ─────────────────────────────────────────────────────────────
// Frontend-only view models (not part of the wire contract)
// ─────────────────────────────────────────────────────────────

export type AppMode = "live" | "demo";

export type RunStatus = "idle" | "running" | "completed" | "failed";

export type StageStatus = "queued" | "running" | "done" | "failed";

/** Derived per-stage view state the Pipeline renders. */
export interface StageState {
  stage: Stage;
  status: StageStatus;
  attempt: number;
  message: string;
  /** ms since run start, from the latest event for this stage. */
  elapsedMs: number;
  /** Latest stage_completed.data for this stage (any attempt). */
  output: PipelineEventData;
  /** The stage's input — derived from the previous stage's output. */
  input: PipelineEventData;
}
