/**
 * Pure helpers for reducing a PipelineEvent[] into the view models the UI
 * renders (per-stage state, the final result, the running re-pick info).
 * No React here — kept testable and side-effect free.
 */
import {
  STAGE_ORDER,
  type ExcludedShow,
  type InterestProfile,
  type PipelineEvent,
  type ProfileDump,
  type RunResult,
  type Stage,
  type StageState,
} from "../types.ts";

/** Build the initial queued state for every stage in canonical order. */
export function initialStages(): StageState[] {
  return STAGE_ORDER.map((stage) => ({
    stage,
    status: "queued",
    attempt: 1,
    message: "",
    elapsedMs: 0,
    output: null,
    input: null,
  }));
}

/** The result of folding the event log so far. */
export interface PipelineView {
  stages: StageState[];
  result: RunResult | null;
  /** Cumulative excluded titles surfaced via repick events. */
  excluded: ExcludedShow[];
  /** True once a repick event has been seen this run. */
  repicked: boolean;
  /** The most recent run-level / stage message (for the live status line). */
  lastMessage: string;
  /** Fatal error text, if run_failed / stage_failed occurred. */
  error: string | null;
}

/**
 * Fold the whole event log into a view. Recomputed from scratch on each event
 * batch — the logs are tiny (tens of events) so this is cheap and avoids
 * fragile incremental mutation.
 */
export function reduceEvents(events: PipelineEvent[]): PipelineView {
  const stages = initialStages();
  const byStage = new Map<Stage, StageState>();
  for (const s of stages) byStage.set(s.stage, s);

  let result: RunResult | null = null;
  const excluded: ExcludedShow[] = [];
  let repicked = false;
  let lastMessage = "";
  let error: string | null = null;

  // Track stage outputs to wire the next stage's "input".
  let profileDump: ProfileDump | null = null;
  let interestProfile: InterestProfile | null = null;

  for (const ev of events) {
    if (ev.message) lastMessage = ev.message;
    const st = ev.stage ? byStage.get(ev.stage) : undefined;

    switch (ev.event) {
      case "stage_started":
        if (st) {
          st.status = "running";
          st.attempt = ev.attempt ?? st.attempt;
          st.elapsedMs = ev.elapsed_ms ?? st.elapsedMs;
          if (ev.message) st.message = ev.message;
          // Wire inputs from prior stage outputs.
          if (st.stage === "interest_profiler") st.input = profileDump;
          if (st.stage === "show_matcher") st.input = interestProfile;
        }
        break;

      case "stage_progress":
        if (st && ev.message) st.message = ev.message;
        break;

      case "stage_completed":
        if (st) {
          st.status = "done";
          st.attempt = ev.attempt ?? st.attempt;
          st.elapsedMs = ev.elapsed_ms ?? st.elapsedMs;
          if (ev.message) st.message = ev.message;
          st.output = ev.data ?? st.output;
          if (st.stage === "insta_reader") {
            profileDump = ev.data as ProfileDump;
          } else if (st.stage === "interest_profiler") {
            interestProfile = ev.data as InterestProfile;
          }
        }
        break;

      case "stage_failed":
        if (st) {
          st.status = "failed";
          st.elapsedMs = ev.elapsed_ms ?? st.elapsedMs;
          const d = ev.data as { error?: string } | null;
          if (d?.error) st.message = d.error;
        }
        break;

      case "repick": {
        repicked = true;
        const d = ev.data as { excluded?: ExcludedShow[] } | null;
        if (d?.excluded) {
          for (const x of d.excluded) {
            if (!excluded.some((e) => e.title === x.title)) excluded.push(x);
          }
        }
        // A repick re-opens the matcher → checker for the new attempt.
        const matcher = byStage.get("show_matcher");
        const checker = byStage.get("streaming_checker");
        if (matcher) {
          matcher.status = "running";
          matcher.attempt = ev.attempt ?? matcher.attempt + 1;
        }
        if (checker) checker.status = "queued";
        break;
      }

      case "run_completed":
        result = (ev.data as RunResult) ?? null;
        // Mark every stage done on completion (defensive).
        for (const s of stages) if (s.status === "running") s.status = "done";
        break;

      case "run_failed": {
        const d = ev.data as { error?: string } | null;
        error = d?.error ?? "The run failed.";
        for (const s of stages) if (s.status === "running") s.status = "failed";
        break;
      }

      case "run_started":
      default:
        break;
    }
  }

  return { stages, result, excluded, repicked, lastMessage, error };
}
