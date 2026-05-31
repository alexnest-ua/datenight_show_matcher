import { JsonViewer } from "./JsonViewer.tsx";
import {
  CheckIcon,
  DotIcon,
  FilmIcon,
  ScanIcon,
  ScreenIcon,
  SparkIcon,
} from "./icons.tsx";
import {
  STAGE_LABELS,
  type Stage,
  type StageState,
  type StageStatus,
} from "../types.ts";

interface StageCardProps {
  state: StageState;
  index: number;
}

/** Decorative "node" glyph per stage. Meaning comes from the title. */
const STAGE_ICONS: Record<Stage, (props: { className?: string }) => React.JSX.Element> = {
  insta_reader: ScanIcon,
  interest_profiler: SparkIcon,
  show_matcher: FilmIcon,
  streaming_checker: ScreenIcon,
};

function statusLabel(status: StageStatus): string {
  switch (status) {
    case "queued":
      return "Queued";
    case "running":
      return "Running";
    case "done":
      return "Done";
    case "failed":
      return "Failed";
  }
}

/** Visual status glyph. Never relies on colour alone — pairs with text label. */
function StatusIndicator({ status }: { status: StageStatus }): React.JSX.Element {
  if (status === "done") {
    return <CheckIcon className="stage-status-icon stage-status-icon--done" />;
  }
  if (status === "running") {
    return (
      <span className="stage-spinner" aria-hidden="true">
        <span className="stage-spinner-ring" />
      </span>
    );
  }
  if (status === "failed") {
    return <DotIcon className="stage-status-icon stage-status-icon--failed" />;
  }
  // queued — hollow circle
  return (
    <span className="stage-status-queued" aria-hidden="true" />
  );
}

export function StageCard({ state, index }: StageCardProps): React.JSX.Element {
  const { stage, status, message, elapsedMs, attempt, input, output } = state;
  const isRunning = status === "running";
  const seconds = (elapsedMs / 1000).toFixed(1);
  const StageIcon = STAGE_ICONS[stage];

  return (
    <li
      className={`stage-card ${isRunning ? "stage-card--active" : ""} stage-card--${status}`}
      aria-current={isRunning ? "step" : undefined}
    >
      <div className="stage-head">
        <span className="stage-node" aria-hidden="true">
          <StageIcon />
          <span className="stage-index">{index + 1}</span>
          {isRunning && <span className="stage-live-dot" />}
        </span>
        <div className="stage-title-wrap">
          <h3 className="stage-title">{STAGE_LABELS[stage]}</h3>
          <p className="stage-message muted">
            {message || (status === "queued" ? "Waiting…" : "")}
          </p>
        </div>
        <div className="stage-meta">
          <span className={`stage-status stage-status--${status}`}>
            <StatusIndicator status={status} />
            <span className="stage-status-text">{statusLabel(status)}</span>
          </span>
          {elapsedMs > 0 && (
            <span className="stage-time" title="Elapsed since run start">
              {seconds}s
            </span>
          )}
          {attempt > 1 && (
            <span className="stage-attempt" title="Re-pick attempt">
              try {attempt}
            </span>
          )}
        </div>
      </div>

      <div className="stage-io">
        {input != null && <JsonViewer label="Input" value={input} />}
        <JsonViewer label="Output" value={output} />
      </div>
    </li>
  );
}
