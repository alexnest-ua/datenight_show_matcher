interface RunButtonProps {
  disabled: boolean;
}

export function RunButton({ disabled }: RunButtonProps): React.JSX.Element {
  return (
    <button type="submit" className="cta-button" disabled={disabled}>
      Find tonight&rsquo;s show{" "}
      <span aria-hidden="true" className="cta-emoji">
        🍿
      </span>
    </button>
  );
}
