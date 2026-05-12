"use client";

import { MarkdownSurface } from "@/components/markdown-surface";
import type { ManifestSurface } from "@/server/types";

type RendererProps = {
  readonly body: string;
  readonly surface?: ManifestSurface;
};

type TocEntry = {
  readonly level: number;
  readonly text: string;
  readonly slug: string;
};

const HEADING_RE = /^(#{1,3})\s+(.+)$/m;

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-");
}

function extractToc(body: string): TocEntry[] {
  const entries: TocEntry[] = [];
  for (const line of body.split("\n")) {
    const match = HEADING_RE.exec(line);
    if (match) {
      const hashes = match[1];
      const text = match[2];
      if (hashes && text) {
        entries.push({ level: hashes.length, text, slug: slugify(text) });
      }
    }
  }
  return entries;
}

/**
 * Two-column layout: sticky ToC sidebar on the left, body on the right.
 * Suited for reference documents that readers scan by section.
 */
export function ReferenceShell({ body }: RendererProps) {
  const toc = extractToc(body);

  return (
    <div className="shell-reference">
      <nav className="shell-reference-toc" aria-label="Table of contents">
        <p className="shell-toc-heading">Contents</p>
        <ul className="shell-toc-list">
          {toc.map((entry) => (
            <li
              key={entry.slug}
              className="shell-toc-item"
              style={{ paddingLeft: `${(entry.level - 1) * 0.75}rem` }}
            >
              <a href={`#${entry.slug}`}>{entry.text}</a>
            </li>
          ))}
        </ul>
      </nav>
      <div className="shell-reference-body">
        <MarkdownSurface body={body} />
      </div>
    </div>
  );
}
