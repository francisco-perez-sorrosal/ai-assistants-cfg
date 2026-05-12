export function ErrorState({
  hint,
  message,
  retry,
  title
}: {
  hint?: string;
  message: string;
  retry?: () => void;
  title: string;
}) {
  return (
    <div className="error-state">
      <h2 className="error-state__title">{title}</h2>
      <p className="error-state__message">{message}</p>
      {hint ? <p className="error-state__hint">{hint}</p> : null}
      {retry ? (
        <button className="error-state__retry" onClick={retry} type="button">
          Try again
        </button>
      ) : null}
    </div>
  );
}
