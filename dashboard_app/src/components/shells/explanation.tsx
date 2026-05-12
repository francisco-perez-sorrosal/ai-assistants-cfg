import { MarkdownSurface } from "@/components/markdown-surface";
import type { ManifestSurface } from "@/server/types";

type RendererProps = {
  readonly body: string;
  readonly surface?: ManifestSurface;
};

/**
 * Wide-prose column layout with a callout aside slot.
 * Suited for explanatory documents that guide understanding over reference lookup.
 * The aside slot is empty in v1; future surfaces may populate it via surface metadata.
 */
export function ExplanationShell({ body }: RendererProps) {
  return (
    <div className="shell-explanation">
      <div className="shell-explanation-body">
        <MarkdownSurface body={body} />
      </div>
      <aside className="explanation-aside" aria-label="Why this matters">
        {/* Callout slot — populated by future surface metadata */}
      </aside>
    </div>
  );
}
