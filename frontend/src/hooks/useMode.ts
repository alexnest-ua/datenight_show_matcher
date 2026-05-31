/**
 * Startup mode detection.
 *
 * Rules (per the spec):
 *  - `?demo=1` in the URL forces DEMO.
 *  - Otherwise probe GET /health (1.5s timeout). If `{status:"ok"}` → LIVE.
 *  - Any failure / timeout → DEMO (silent, never a blank state).
 *  - If VITE_API_BASE is set AND health passes, LIVE is preferred (this falls
 *    out of the same probe — VITE_API_BASE is baked into the fetch URL).
 *
 * Also loads the profile list appropriate to the chosen mode.
 */
import { useEffect, useState } from "react";
import { checkHealth, fetchProfiles } from "../api/client.ts";
import { demoProfiles } from "../api/replay.ts";
import type { AppMode, HealthResponse, ProfileSummary } from "../types.ts";

export interface ModeState {
  /** null while detecting. */
  mode: AppMode | null;
  health: HealthResponse | null;
  profiles: ProfileSummary[];
}

function demoForced(): boolean {
  if (typeof window === "undefined") return false;
  return new URLSearchParams(window.location.search).get("demo") === "1";
}

export function useMode(): ModeState {
  const [state, setState] = useState<ModeState>({
    mode: null,
    health: null,
    profiles: [],
  });

  useEffect(() => {
    let active = true;

    async function detect(): Promise<void> {
      if (demoForced()) {
        if (active) {
          setState({ mode: "demo", health: null, profiles: demoProfiles() });
        }
        return;
      }

      const health = await checkHealth();
      if (!active) return;

      if (health) {
        const profiles = await fetchProfiles();
        if (!active) return;
        // If the backend exposes no profiles, still LIVE — free-text handle works.
        setState({ mode: "live", health, profiles });
      } else {
        setState({ mode: "demo", health: null, profiles: demoProfiles() });
      }
    }

    void detect();
    return () => {
      active = false;
    };
  }, []);

  return state;
}
