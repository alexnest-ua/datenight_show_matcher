import type { AppMode } from "../types.ts";

interface ModePillProps {
  mode: AppMode | null;
}

/**
 * LIVE (green) when a backend is connected, DEMO (amber) when replaying a
 * recording. While detecting, shows a neutral placeholder so layout is stable
 * (no CLS).
 */
export function ModePill({ mode }: ModePillProps): React.JSX.Element {
  if (mode === null) {
    return (
      <span className="mode-pill mode-pill--pending" aria-live="polite">
        <span className="mode-dot" aria-hidden="true" />
        Connecting…
      </span>
    );
  }
  const isLive = mode === "live";
  return (
    <span
      className={`mode-pill ${isLive ? "mode-pill--live" : "mode-pill--demo"}`}
      title={
        isLive
          ? "Connected to a live backend — real pipeline via SSE."
          : "No backend reachable — replaying a bundled recording."
      }
    >
      <span className="mode-dot" aria-hidden="true" />
      {isLive ? "LIVE" : "DEMO"}
    </span>
  );
}
