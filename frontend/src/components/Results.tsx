import { ExcludedList } from "./ExcludedList.tsx";
import { ShowCard } from "./ShowCard.tsx";
import type { RunResult } from "../types.ts";

interface ResultsProps {
  result: RunResult;
  onReplay: () => void;
  onTryAnother: () => void;
}

export function Results({
  result,
  onReplay,
  onTryAnother,
}: ResultsProps): React.JSX.Element {
  const { picks, excluded, profile, attempts } = result;

  return (
    <section className="section results" aria-labelledby="results-heading">
      <div className="results-head">
        <h2 id="results-heading" className="section-title">
          Tonight&rsquo;s picks{" "}
          <span className="results-sparkle" aria-hidden="true">
            ✨
          </span>
        </h2>
        <p className="muted">
          {profile.aesthetic_vibe}
          {attempts > 1 && (
            <span className="results-attempts"> · settled after {attempts} tries</span>
          )}
        </p>
      </div>

      {picks.length > 0 ? (
        <ol className="show-list">
          {picks.map((pick, i) => (
            <ShowCard key={pick.title} pick={pick} rank={i + 1} />
          ))}
        </ol>
      ) : (
        <p className="muted results-empty">
          None of the matched shows were on your subscriptions, and we&rsquo;d
          already ruled out the rest. Try another profile, or add a streaming
          service.
        </p>
      )}

      <ExcludedList excluded={excluded} />

      <div className="results-actions">
        <button type="button" className="cta-button" onClick={onReplay}>
          Replay
        </button>
        <button type="button" className="ghost-button" onClick={onTryAnother}>
          Try another profile
        </button>
      </div>
    </section>
  );
}
