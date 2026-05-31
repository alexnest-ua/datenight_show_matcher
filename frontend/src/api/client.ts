/**
 * LIVE-mode backend client: health probe, profiles fetch, and an EventSource
 * helper for the SSE pipeline stream. See docs/contracts.md §4.
 */
import type {
  HealthResponse,
  PipelineEvent,
  ProfileSummary,
} from "../types.ts";

/** Same-origin by default (dev proxy / same-host deploy). */
export const API_BASE: string = import.meta.env.VITE_API_BASE ?? "";

const HEALTH_TIMEOUT_MS = 1500;

/** Build an absolute-or-proxied URL for an API path. */
function url(path: string): string {
  return `${API_BASE}${path}`;
}

/**
 * Probe the backend. Returns the parsed health body on `{status:"ok"}`,
 * otherwise null (any error, timeout, non-ok status). Never throws.
 */
export async function checkHealth(): Promise<HealthResponse | null> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), HEALTH_TIMEOUT_MS);
  try {
    const res = await fetch(url("/health"), {
      method: "GET",
      signal: controller.signal,
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return null;
    const body = (await res.json()) as HealthResponse;
    return body?.status === "ok" ? body : null;
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

/** Fetch the known-handle list for the picker. Returns [] on any failure. */
export async function fetchProfiles(): Promise<ProfileSummary[]> {
  try {
    const res = await fetch(url("/api/profiles"), {
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return [];
    const body = (await res.json()) as unknown;
    return Array.isArray(body) ? (body as ProfileSummary[]) : [];
  } catch {
    return [];
  }
}

export interface StreamHandlers {
  onEvent: (event: PipelineEvent) => void;
  onError: (message: string) => void;
}

/**
 * Open the live SSE pipeline stream for a handle. Default `message` events
 * carry a JSON `PipelineEvent` in `data` (per contracts.md). Returns a closer
 * that the caller MUST invoke on unmount / new run; we also auto-close on
 * run_completed / run_failed.
 */
export function openStream(handle: string, handlers: StreamHandlers): () => void {
  const src = url(`/api/stream?handle=${encodeURIComponent(handle)}`);
  const es = new EventSource(src);
  let closed = false;

  const close = (): void => {
    if (closed) return;
    closed = true;
    es.close();
  };

  es.onmessage = (msg: MessageEvent<string>) => {
    let parsed: PipelineEvent;
    try {
      parsed = JSON.parse(msg.data) as PipelineEvent;
    } catch {
      handlers.onError("Received a malformed event from the stream.");
      return;
    }
    handlers.onEvent(parsed);
    if (parsed.event === "run_completed" || parsed.event === "run_failed") {
      close();
    }
  };

  es.onerror = () => {
    // This is a short, one-shot stream — we don't want EventSource's automatic
    // reconnect. Normal completion already set `closed` in onmessage, so any
    // onerror while still open means the run won't finish (failed connect or a
    // mid-stream drop, where readyState is CONNECTING not CLOSED). Close and
    // surface it once rather than silently stalling.
    if (closed) return;
    close();
    handlers.onError("Connection to the live stream was lost.");
  };

  return close;
}
