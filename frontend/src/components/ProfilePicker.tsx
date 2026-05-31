import { useId, useState } from "react";
import { RunButton } from "./RunButton.tsx";
import type { AppMode, ProfileSummary } from "../types.ts";

interface ProfilePickerProps {
  mode: AppMode | null;
  profiles: ProfileSummary[];
  /** Currently selected handle (controlled). */
  selected: string | null;
  onSelect: (handle: string) => void;
  onRun: (handle: string) => void;
  disabled: boolean;
}

/**
 * The idle screen: a headline, the known-handle picker, an optional free-text
 * @handle input (LIVE only), and the primary CTA.
 */
export function ProfilePicker({
  mode,
  profiles,
  selected,
  onSelect,
  onRun,
  disabled,
}: ProfilePickerProps): React.JSX.Element {
  const inputId = useId();
  const [freeText, setFreeText] = useState("");

  // The handle that will actually run: free-text wins when non-empty (live).
  const liveFree = mode === "live" ? freeText.trim() : "";
  const effectiveHandle = liveFree || selected || "";

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    if (effectiveHandle && !disabled) onRun(effectiveHandle);
  };

  return (
    <section className="section picker" aria-labelledby="picker-heading">
      <div className="picker-intro">
        <span className="eyebrow mono-label">
          <span className="eyebrow-dot" aria-hidden="true" />
          4-stage taste pipeline
        </span>
        <h1 id="picker-heading" className="headline">
          Find tonight&rsquo;s perfect{" "}
          <span className="gradient-text">date-night show</span>
        </h1>
        <p className="subhead muted">
          Pick an Instagram profile and we&rsquo;ll profile their taste, then match
          three shows you can actually stream on Netflix or HBO.
        </p>
      </div>

      <form className="picker-form" onSubmit={handleSubmit}>
        <fieldset className="profile-choices">
          <legend className="field-legend">Choose a profile</legend>
          <ul className="profile-list">
            {profiles.map((p) => {
              const isSel = selected === p.handle && !liveFree;
              return (
                <li key={p.handle}>
                  <button
                    type="button"
                    className={`profile-chip ${isSel ? "profile-chip--active" : ""}`}
                    aria-pressed={isSel}
                    onClick={() => {
                      setFreeText("");
                      onSelect(p.handle);
                    }}
                  >
                    <span className="profile-handle">{p.handle}</span>
                    <span className="profile-name muted">{p.display_name}</span>
                  </button>
                </li>
              );
            })}
          </ul>
          {profiles.length === 0 && (
            <p className="muted">No saved profiles — enter a handle below.</p>
          )}
        </fieldset>

        {mode === "live" && (
          <div className="field">
            <label htmlFor={inputId} className="field-label">
              …or enter any Instagram handle
            </label>
            <div className="input-affix">
              <span className="input-prefix" aria-hidden="true">
                @
              </span>
              <input
                id={inputId}
                type="text"
                className="text-input"
                inputMode="text"
                autoComplete="off"
                spellCheck={false}
                placeholder="some_handle"
                value={freeText}
                onChange={(e) => setFreeText(e.target.value)}
              />
            </div>
          </div>
        )}

        <RunButton disabled={disabled || !effectiveHandle} />
      </form>
    </section>
  );
}
