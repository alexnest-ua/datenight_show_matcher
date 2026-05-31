import { Logo } from "./Logo.tsx";
import { ModePill } from "./ModePill.tsx";
import { ThemeToggle } from "./ThemeToggle.tsx";
import type { Theme } from "../hooks/useTheme.ts";
import type { AppMode } from "../types.ts";

interface HeaderProps {
  mode: AppMode | null;
  theme: Theme;
  onToggleTheme: () => void;
}

export function Header({ mode, theme, onToggleTheme }: HeaderProps): React.JSX.Element {
  return (
    <header className="site-header">
      <div className="container site-header-inner">
        <div className="brand">
          <Logo />
          <span className="brand-tag">DateNight Show Matcher</span>
        </div>
        <div className="header-controls">
          <ModePill mode={mode} />
          <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        </div>
      </div>
    </header>
  );
}
