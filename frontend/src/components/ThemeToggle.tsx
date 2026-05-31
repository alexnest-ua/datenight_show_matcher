import { MoonIcon, SunIcon } from "./icons.tsx";
import type { Theme } from "../hooks/useTheme.ts";

interface ThemeToggleProps {
  theme: Theme;
  onToggle: () => void;
}

export function ThemeToggle({ theme, onToggle }: ThemeToggleProps): React.JSX.Element {
  const next = theme === "dark" ? "light" : "dark";
  return (
    <button
      type="button"
      className="icon-button"
      onClick={onToggle}
      aria-label={`Switch to ${next} theme`}
      aria-pressed={theme === "light"}
    >
      {theme === "dark" ? <MoonIcon /> : <SunIcon />}
    </button>
  );
}
