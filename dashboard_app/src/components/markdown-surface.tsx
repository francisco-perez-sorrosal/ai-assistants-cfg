import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// react-markdown escapes raw HTML by default (security posture: no rehype-raw).
// Project markdown bodies (.ai-state/DESIGN.md, docs/architecture.md, etc.) embed
// diagrams as raw <img> tags and surround sections with <!-- OWNER: ... --> comments.
// Both show as literal escaped text unless preprocessed. This helper normalises them
// before react-markdown sees the content, without relaxing the no-raw-HTML posture:
//   1. Strip HTML comments (<!-- ... -->) — purely cosmetic; agents read the source.
//   2. Convert standalone <img src="..." alt="..."> to markdown image syntax ![alt](src)
//      so react-markdown renders them as real <img> elements.
// Markdown image syntax (![alt](url)) is untouched — it already renders correctly.
export function prepareMarkdownBody(raw: string): string {
  // Step 1: strip HTML comments
  const noComments = raw.replace(/<!--[\s\S]*?-->/g, "");

  // Step 2: convert raw <img ...> tags to markdown image syntax.
  // Handles both double- and single-quoted attribute values, optional whitespace,
  // self-closing slash, and any attribute order.
  const noRawImg = noComments.replace(
    /<img\s([^>]*?)>/gi,
    (_match: string, attrs: string) => {
      const srcMatch = attrs.match(/src=["']([^"']*)["']/i);
      const altMatch = attrs.match(/alt=["']([^"']*)["']/i);
      const src = srcMatch ? srcMatch[1] : "";
      const alt = altMatch ? altMatch[1] : "";
      if (!src) return "";
      return `![${alt}](${src})`;
    }
  );

  return noRawImg;
}

export function MarkdownSurface({ body }: { body: string }) {
  return (
    <div className="markdown-surface">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {prepareMarkdownBody(body)}
      </ReactMarkdown>
    </div>
  );
}
