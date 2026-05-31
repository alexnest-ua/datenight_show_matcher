import { PlatformBadge } from "./PlatformBadge.tsx";
import type { FinalPick } from "../types.ts";

interface ShowCardProps {
  pick: FinalPick;
  rank: number;
}

export function ShowCard({ pick, rank }: ShowCardProps): React.JSX.Element {
  return (
    <article className="show-card" aria-label={`Rank ${rank}: ${pick.title}`}>
      <div className="show-card-top">
        <span className="show-rank" aria-hidden="true">
          {rank}
        </span>
        <div className="show-title-wrap">
          <h3 className="show-title">{pick.title}</h3>
          {pick.year != null && <p className="show-year muted">{pick.year}</p>}
        </div>
      </div>

      {pick.genres.length > 0 && (
        <ul className="genre-chips" aria-label="Genres">
          {pick.genres.map((g) => (
            <li key={g} className="genre-chip">
              {g}
            </li>
          ))}
        </ul>
      )}

      <p className="show-why">{pick.why}</p>

      <div className="show-platforms">
        <span className="show-platforms-label muted">Stream on</span>
        <div className="platform-row">
          {pick.platforms.map((p) => (
            <PlatformBadge key={p} platform={p} />
          ))}
        </div>
      </div>
    </article>
  );
}
