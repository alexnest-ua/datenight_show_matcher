import type { ExcludedShow } from "../types.ts";

interface ExcludedListProps {
  excluded: ExcludedShow[];
}

/** Small "Not available, re-picked" list shown beneath the results. */
export function ExcludedList({ excluded }: ExcludedListProps): React.JSX.Element | null {
  if (excluded.length === 0) return null;
  return (
    <div className="excluded">
      <h3 className="excluded-title">Not available — re-picked</h3>
      <ul className="excluded-list">
        {excluded.map((x) => (
          <li key={x.title} className="excluded-item">
            <span className="excluded-name">{x.title}</span>
            <span className="excluded-reason muted">{x.reason}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
