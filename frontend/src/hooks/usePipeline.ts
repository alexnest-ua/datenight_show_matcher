/**
 * Drives a single pipeline run in either LIVE (SSE) or DEMO (replay) mode and
 * exposes the reduced view (events, per-stage state, result, status). The
 * caller picks the handle and calls `start`; the hook owns the connection and
 * tears it down on a new run / unmount / completion.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { openStream } from "../api/client.ts";
import { replayRun } from "../api/replay.ts";
import { reduceEvents, type PipelineView } from "../lib/events.ts";
import type { AppMode, PipelineEvent, RunStatus } from "../types.ts";

export interface PipelineController {
  status: RunStatus;
  events: PipelineEvent[];
  view: PipelineView;
  /** The handle of the active / last run. */
  handle: string | null;
  start: (handle: string) => void;
  reset: () => void;
}

export function usePipeline(mode: AppMode | null): PipelineController {
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const [status, setStatus] = useState<RunStatus>("idle");
  const [handle, setHandle] = useState<string | null>(null);

  // Active connection/replay canceller.
  const cancelRef = useRef<(() => void) | null>(null);

  const teardown = useCallback(() => {
    cancelRef.current?.();
    cancelRef.current = null;
  }, []);

  const start = useCallback(
    (rawHandle: string) => {
      const h = rawHandle.trim();
      if (!h || !mode) return;

      teardown();
      setEvents([]);
      setStatus("running");
      setHandle(h);

      const onEvent = (ev: PipelineEvent): void => {
        setEvents((prev) => [...prev, ev]);
        if (ev.event === "run_completed") setStatus("completed");
        if (ev.event === "run_failed") setStatus("failed");
      };
      const onError = (message: string): void => {
        setEvents((prev) => [
          ...prev,
          {
            seq: prev.length,
            event: "run_failed",
            stage: null,
            elapsed_ms: 0,
            message,
            data: { error: message },
          },
        ]);
        setStatus("failed");
      };

      cancelRef.current =
        mode === "live"
          ? openStream(h, { onEvent, onError })
          : replayRun(h, { onEvent, onError });
    },
    [mode, teardown],
  );

  const reset = useCallback(() => {
    teardown();
    setEvents([]);
    setStatus("idle");
    setHandle(null);
  }, [teardown]);

  // Tear down on unmount.
  useEffect(() => teardown, [teardown]);

  const view = useMemo(() => reduceEvents(events), [events]);

  return { status, events, view, handle, start, reset };
}
