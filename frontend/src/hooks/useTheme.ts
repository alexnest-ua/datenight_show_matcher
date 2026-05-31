/**
 * Theme controller. Dark is the product default; a stored user choice
 * (localStorage) always wins and persists across reloads.
 */
import { useCallback, useEffect, useState } from "react";

export type Theme = "dark" | "light";

const STORAGE_KEY = "playfix-theme";

function readStored(): Theme | null {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    return v === "dark" || v === "light" ? v : null;
  } catch {
    return null;
  }
}

function initialTheme(): Theme {
  // Dark is the product default; a stored user choice always wins.
  return readStored() ?? "dark";
}

export function useTheme(): { theme: Theme; toggle: () => void } {
  const [theme, setTheme] = useState<Theme>(initialTheme);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const toggle = useCallback(() => {
    setTheme((prev) => {
      const next: Theme = prev === "dark" ? "light" : "dark";
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch {
        /* storage may be unavailable (private mode) — ignore */
      }
      return next;
    });
  }, []);

  return { theme, toggle };
}
