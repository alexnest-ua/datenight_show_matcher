/**
 * PlayFix wordmark, recreated as styled text per docs/brand.md (offline-safe,
 * no hotlinking): "Play" in --text + "Fix" in --primary, Inter 700.
 *
 * NOTE: the official PlayFix SVG logo can be dropped in here later — replace the
 * <span> wordmark with an inline <svg> (so currentColor / theming still work),
 * keeping the same `.logo` wrapper and the `aria-label` for the accessible name.
 */
export function Logo(): React.JSX.Element {
  return (
    <span className="logo" aria-label="PlayFix">
      <span className="logo-play" aria-hidden="true">
        Play
      </span>
      <span className="logo-fix" aria-hidden="true">
        Fix
      </span>
    </span>
  );
}
