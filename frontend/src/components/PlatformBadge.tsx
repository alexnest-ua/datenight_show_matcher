interface PlatformBadgeProps {
  platform: string;
}

const LABELS: Record<string, string> = {
  netflix: "Netflix",
  hbo: "HBO Max",
  prime: "Prime Video",
};

/** Coloured per brand: Netflix red, HBO purple, Prime blue. */
export function PlatformBadge({ platform }: PlatformBadgeProps): React.JSX.Element {
  const key = platform.toLowerCase();
  const label = LABELS[key] ?? platform;
  return (
    <span className={`platform-badge platform-badge--${key}`}>{label}</span>
  );
}
