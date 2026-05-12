import { MarkdownSurface } from "@/components/markdown-surface";
import type { ManifestSurface } from "@/server/types";

type RendererProps = {
  readonly body: string;
  readonly surface?: ManifestSurface;
};

/** Plain card shell — default fallback for any unrecognized content type. */
export function DefaultShell({ body }: RendererProps) {
  return (
    <div className="shell-default">
      <MarkdownSurface body={body} />
    </div>
  );
}
