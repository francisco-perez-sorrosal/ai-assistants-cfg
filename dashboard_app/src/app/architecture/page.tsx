import path from "node:path";

import { ArtifactCard } from "@/components/artifact-card";
import { Chip } from "@/components/chrome/chip";
import { EducationalPopover } from "@/components/educational-popover";
import { EmptyState } from "@/components/empty-state";
import { MarkdownSurface } from "@/components/markdown-surface";
import { DiagramViewer } from "@/components/viz/diagram-viewer";
import { getConfig } from "@/lib/config";
import { getArchitectureData } from "@/server/view-models/architecture";
import type { AacRegion } from "@/server/aac/parse-fences";

// ─── AaC region badge ────────────────────────────────────────────────────────

function AacBadge({ region }: { readonly region: AacRegion }) {
  if (region.kind === "plain") {
    return null;
  }

  const source = typeof region.attrs["source"] === "string" ? region.attrs["source"] : undefined;
  const view = typeof region.attrs["view"] === "string" ? region.attrs["view"] : undefined;
  const owner = typeof region.attrs["owner"] === "string" ? region.attrs["owner"] : undefined;

  if (region.kind === "generated") {
    const label = [
      "Generated",
      source !== undefined ? `source=${source}` : null,
      view !== undefined ? `view=${view}` : null
    ]
      .filter(Boolean)
      .join(" · ");
    return (
      <div className="aac-badge aac-badge--generated">
        <Chip variant="neutral">{label}</Chip>
      </div>
    );
  }

  // authored
  const label = ["Authored", owner !== undefined ? `owner=${owner}` : null]
    .filter(Boolean)
    .join(" · ");
  return (
    <div className="aac-badge aac-badge--authored">
      <Chip variant="neutral">{label}</Chip>
    </div>
  );
}

// ─── AaC region list ─────────────────────────────────────────────────────────

function AacRegionList({ regions }: { readonly regions: AacRegion[] }) {
  return (
    <div className="aac-regions">
      {regions.map((region, idx) => (
        // eslint-disable-next-line react/no-array-index-key
        <div key={idx} className={`aac-region aac-region--${region.kind}`}>
          <AacBadge region={region} />
          <MarkdownSurface body={region.content} />
        </div>
      ))}
    </div>
  );
}

// ─── Friendly diagram name ────────────────────────────────────────────────────

function friendlyDiagramLabel(diagramPath: string, projectRoot: string): string {
  const rel = path.relative(projectRoot, diagramPath);
  const base = path.basename(diagramPath, ".svg");
  // Collapse leading path prefix to keep the label short but identifiable
  return `${base} (${rel})`;
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default async function ArchitecturePage() {
  const cfg = getConfig();
  const data = await getArchitectureData(cfg.projectRoot);

  const hasContent = data.design !== null || data.guide !== null || data.diagrams.length > 0;

  return (
    <section className="page-card">
      <header className="page-intro">
        <div>
          <p className="eyebrow">Status surface</p>
          <h2>Architecture</h2>
          <p>
            Design-target architecture, developer guide, and rendered diagrams from
            the live project filesystem.{" "}
            <EducationalPopover
              title="What is this?"
              body="The architecture surfaces show the design-target (DESIGN.md) and code-verified (architecture.md) views, plus the rendered diagrams."
              href="docs/architecture.md"
            />
          </p>
        </div>
        <aside>
          <span>Source contract</span>
          <strong>
            Read <code>.ai-state/DESIGN.md</code>, <code>docs/architecture.md</code>, and SVGs
            directly.
          </strong>
        </aside>
      </header>

      {!hasContent ? (
        <EmptyState
          title="No architecture artifacts found"
          body="Run a systems-architect pass for the target project to generate the architecture surfaces."
          producerPath=".ai-state/DESIGN.md"
        />
      ) : (
        <div className="architecture-body">
          {/* ── Explicit diagrams list ─────────────────────────────────────── */}
          {data.diagrams.length > 0 ? (
            <section className="section-card">
              <h3>Diagrams</h3>
              <div className="architecture-diagrams">
                {data.diagrams.map((diagram) => (
                  <ArtifactCard
                    key={diagram.path}
                    title={friendlyDiagramLabel(diagram.path, cfg.projectRoot)}
                    defaultOpen={true}
                  >
                    <DiagramViewer
                      svg={diagram.markup ?? ""}
                      label={friendlyDiagramLabel(diagram.path, cfg.projectRoot)}
                    />
                  </ArtifactCard>
                ))}
              </div>
            </section>
          ) : null}

          {/* ── DESIGN.md — rendered via AaC regions ──────────────────────── */}
          {data.design !== null ? (
            <ArtifactCard title="Design target" meta={<Chip variant="neutral">.ai-state/DESIGN.md</Chip>}>
              {data.regions.length > 0 ? (
                <AacRegionList regions={data.regions} />
              ) : (
                <MarkdownSurface body={data.design.body} />
              )}
            </ArtifactCard>
          ) : null}

          {/* ── docs/architecture.md ──────────────────────────────────────── */}
          {data.guide !== null ? (
            <ArtifactCard title="Developer guide" meta={<Chip variant="neutral">docs/architecture.md</Chip>}>
              <MarkdownSurface body={data.guide.body} />
            </ArtifactCard>
          ) : null}
        </div>
      )}
    </section>
  );
}
