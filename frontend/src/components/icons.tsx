/**
 * Inline SVG icons. Inline (not <img>) so `currentColor` + CSS sizing work.
 * Decorative icons get aria-hidden; meaningful ones receive a label from the
 * calling component (e.g. the theme toggle's accessible button name).
 */

interface IconProps {
  className?: string;
}

export function SunIcon({ className }: IconProps): React.JSX.Element {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      width="20"
      height="20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </svg>
  );
}

export function MoonIcon({ className }: IconProps): React.JSX.Element {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      width="20"
      height="20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
    </svg>
  );
}

/** A small filled dot used by status indicators. */
export function DotIcon({ className }: IconProps): React.JSX.Element {
  return (
    <svg
      className={className}
      viewBox="0 0 12 12"
      width="12"
      height="12"
      aria-hidden="true"
      focusable="false"
    >
      <circle cx="6" cy="6" r="5" fill="currentColor" />
    </svg>
  );
}

/** Checkmark for "available". */
export function CheckIcon({ className }: IconProps): React.JSX.Element {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      width="16"
      height="16"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.4"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

/** Chevron used by the expandable JSON panels. */
export function ChevronIcon({ className }: IconProps): React.JSX.Element {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      width="16"
      height="16"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}

/**
 * Per-stage glyphs for the pipeline "node" containers. Decorative — the stage
 * title carries the meaning, so all are aria-hidden. currentColor lets the node
 * container drive the colour (muted → primary when running, green when done).
 */
function StageSvg({
  className,
  children,
}: IconProps & { children: React.ReactNode }): React.JSX.Element {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      width="20"
      height="20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {children}
    </svg>
  );
}

/** Stage 1 — Insta Reader: camera / scan. */
export function ScanIcon({ className }: IconProps): React.JSX.Element {
  return (
    <StageSvg className={className}>
      <rect x="3" y="3" width="18" height="18" rx="5" />
      <circle cx="12" cy="12" r="3.5" />
      <circle cx="17.2" cy="6.8" r="1" fill="currentColor" stroke="none" />
    </StageSvg>
  );
}

/** Stage 2 — Interest Profiler: sparkle / taste. */
export function SparkIcon({ className }: IconProps): React.JSX.Element {
  return (
    <StageSvg className={className}>
      <path d="M12 3v4M12 17v4M3 12h4M17 12h4M12 8.5 13.6 12 12 15.5 10.4 12z" />
    </StageSvg>
  );
}

/** Stage 3 — Show Matcher: film clapper. */
export function FilmIcon({ className }: IconProps): React.JSX.Element {
  return (
    <StageSvg className={className}>
      <rect x="3" y="4" width="18" height="16" rx="3" />
      <path d="M3 9h18M8.5 4l-2 5M13.5 4l-2 5M18.5 4l-2 5" />
    </StageSvg>
  );
}

/** Stage 4 — Streaming Checker: screen / monitor. */
export function ScreenIcon({ className }: IconProps): React.JSX.Element {
  return (
    <StageSvg className={className}>
      <rect x="2.5" y="4" width="19" height="13" rx="3" />
      <path d="M8 21h8M12 17v4" />
    </StageSvg>
  );
}
