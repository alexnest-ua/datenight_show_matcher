import { useId, useState } from "react";
import { ChevronIcon } from "./icons.tsx";
import type { PipelineEventData } from "../types.ts";

interface JsonViewerProps {
  label: string;
  value: PipelineEventData;
  /** Start expanded? Defaults to collapsed to keep the pipeline compact. */
  defaultOpen?: boolean;
}

/**
 * An expandable, pretty-printed JSON panel for a stage's input / output.
 * Uses <details>-style disclosure built from a button + region for full
 * keyboard control and an explicit aria-expanded.
 */
export function JsonViewer({
  label,
  value,
  defaultOpen = false,
}: JsonViewerProps): React.JSX.Element {
  const [open, setOpen] = useState(defaultOpen);
  const regionId = useId();
  const empty = value === null || value === undefined;
  const pretty = empty ? "—" : JSON.stringify(value, null, 2);

  return (
    <div className="json-viewer">
      <button
        type="button"
        className="json-toggle"
        aria-expanded={open}
        aria-controls={regionId}
        onClick={() => setOpen((v) => !v)}
        disabled={empty}
      >
        <ChevronIcon className={`json-chevron ${open ? "json-chevron--open" : ""}`} />
        <span className="json-label">{label}</span>
        {empty && <span className="json-empty muted">not yet</span>}
      </button>
      {open && !empty && (
        <pre id={regionId} className="json-block" tabIndex={0}>
          <code>{pretty}</code>
        </pre>
      )}
    </div>
  );
}
