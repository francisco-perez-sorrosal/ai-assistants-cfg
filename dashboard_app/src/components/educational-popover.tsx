"use client";

export function EducationalPopover({
  body,
  href,
  title
}: {
  body: string;
  href?: string;
  title: string;
}) {
  return (
    <span className="educational-popover">
      <span
        aria-label={`What is ${title}?`}
        className="educational-popover__trigger"
        role="button"
        tabIndex={0}
      >
        ?
      </span>
      <span className="educational-popover__panel" role="tooltip">
        <strong className="educational-popover__title">{title}</strong>
        <span className="educational-popover__body">{body}</span>
        {href ? (
          <a
            className="educational-popover__link"
            href={href}
            rel="noopener noreferrer"
            target="_blank"
          >
            Learn more →
          </a>
        ) : null}
      </span>
    </span>
  );
}
