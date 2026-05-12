export function EmptyState({
  body,
  producerPath,
  title
}: {
  body: string;
  producerPath?: string;
  title: string;
}) {
  return (
    <section className="empty-state">
      <h2>{title}</h2>
      <p>{body}</p>
      {producerPath ? (
        <p className="empty-state__producer">
          Produced by: <code className="empty-state__producer-path">{producerPath}</code>
        </p>
      ) : null}
    </section>
  );
}
