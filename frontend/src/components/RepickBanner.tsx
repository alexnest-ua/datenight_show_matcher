import type { ExcludedShow } from "../types.ts";

interface RepickBannerProps {
  excluded: ExcludedShow[];
}

/**
 * Amber banner shown when a repick occurs: lists what was excluded and why.
 * role="status" so assistive tech announces it without stealing focus.
 */
export function RepickBanner({ excluded }: RepickBannerProps): React.JSX.Element {
  return (
    <div className="repick-banner" role="status">
      <p className="repick-title">
        <span className="repick-icon" aria-hidden="true">
          ↻
        </span>
        Re-picking — a show wasn&rsquo;t on your subscriptions
      </p>
      <ul className="repick-list">
        {excluded.map((x) => (
          <li key={x.title} className="repick-item">
            <span className="repick-name">{x.title}</span>
            <span className="repick-reason muted">{x.reason}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
