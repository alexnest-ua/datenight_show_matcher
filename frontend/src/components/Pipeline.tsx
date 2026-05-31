import { RepickBanner } from "./RepickBanner.tsx";
import { StageCard } from "./StageCard.tsx";
import type { PipelineView } from "../lib/events.ts";
import type { RunStatus } from "../types.ts";

interface PipelineProps {
  view: PipelineView;
  status: RunStatus;
  handle: string;
}

/**
 * The pipeline centrepiece: four stage cards in order plus the re-pick banner.
 * The whole region is aria-live="polite" so screen-reader users hear progress
 * as stages flip status and messages update.
 */
export function Pipeline({ view, status, handle }: PipelineProps): React.JSX.Element {
  const { stages, repicked, excluded, lastMessage } = view;

  return (
    <section className="section pipeline" aria-labelledby="pipeline-heading">
      <div className="pipeline-head">
        <h2 id="pipeline-heading" className="section-title">
          Matching shows for{" "}
          <span className="pipeline-handle">{handle}</span>
        </h2>
        <p className="pipeline-status muted" aria-live="polite">
          {status === "running" && (
            <span className="pipeline-live-dot" aria-hidden="true" />
          )}
          {status === "running" && (lastMessage || "Working…")}
          {status === "completed" && "Done — your picks are ready."}
          {status === "failed" && "Something went wrong with this run."}
        </p>
      </div>

      {repicked && excluded.length > 0 && <RepickBanner excluded={excluded} />}

      {/* aria-live region carries staged progress to assistive tech. */}
      <ol className="stage-list" aria-live="polite">
        {stages.map((s, i) => (
          <StageCard key={s.stage} state={s} index={i} />
        ))}
      </ol>
    </section>
  );
}
