import { useCallback, useEffect, useState } from "react";
import { Header } from "./components/Header.tsx";
import { Pipeline } from "./components/Pipeline.tsx";
import { ProfilePicker } from "./components/ProfilePicker.tsx";
import { Results } from "./components/Results.tsx";
import { useMode } from "./hooks/useMode.ts";
import { usePipeline } from "./hooks/usePipeline.ts";
import { useTheme } from "./hooks/useTheme.ts";

export function App(): React.JSX.Element {
  const { theme, toggle } = useTheme();
  const { mode, profiles } = useMode();
  const pipeline = usePipeline(mode);
  const [selected, setSelected] = useState<string | null>(null);

  // Pre-select the first known profile once they load (nice default; users can
  // change it). Only when nothing is selected yet.
  useEffect(() => {
    if (selected === null && profiles.length > 0) {
      setSelected(profiles[0]?.handle ?? null);
    }
  }, [profiles, selected]);

  const handleRun = useCallback(
    (handle: string) => {
      pipeline.start(handle);
    },
    [pipeline],
  );

  const handleReplay = useCallback(() => {
    if (pipeline.handle) pipeline.start(pipeline.handle);
  }, [pipeline]);

  const handleTryAnother = useCallback(() => {
    pipeline.reset();
  }, [pipeline]);

  const showPipeline = pipeline.status !== "idle";
  const showResults =
    pipeline.status === "completed" && pipeline.view.result !== null;

  return (
    <div className="app">
      {/* Decorative ambient void: faint grid + warm radial blobs. */}
      <div className="void-bg" aria-hidden="true">
        <div className="void-grid" />
        <div className="void-blob void-blob--primary" />
        <div className="void-blob void-blob--accent" />
      </div>

      <a className="skip-link" href="#main">
        Skip to content
      </a>

      <Header mode={mode} theme={theme} onToggleTheme={toggle} />

      <main id="main" className="main container" tabIndex={-1}>
        {!showPipeline && (
          <ProfilePicker
            mode={mode}
            profiles={profiles}
            selected={selected}
            onSelect={setSelected}
            onRun={handleRun}
            disabled={mode === null}
          />
        )}

        {showPipeline && (
          <Pipeline
            view={pipeline.view}
            status={pipeline.status}
            handle={pipeline.handle ?? ""}
          />
        )}

        {showResults && pipeline.view.result && (
          <Results
            result={pipeline.view.result}
            onReplay={handleReplay}
            onTryAnother={handleTryAnother}
          />
        )}

        {pipeline.status === "failed" && (
          <div className="run-error" role="alert">
            <p>{pipeline.view.error ?? "The run failed."}</p>
            <button type="button" className="ghost-button" onClick={handleTryAnother}>
              Back to profiles
            </button>
          </div>
        )}
      </main>

      <footer className="site-footer">
        <div className="container">
          <p>
            PlayFix · DateNight Show Matcher — a demo of a 4-stage Claude agent
            pipeline.
          </p>
        </div>
      </footer>
    </div>
  );
}
