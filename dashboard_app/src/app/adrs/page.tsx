import { EducationalPopover } from "@/components/educational-popover";
import { EmptyState } from "@/components/empty-state";
import { getConfig } from "@/lib/config";
import { getAdrData } from "@/server/view-models/adrs";

import { AdrFilterClient } from "./adr-filter-client";
import { AdrGraphClient } from "./adr-graph-client";

export default async function AdrsPage() {
  const cfg = getConfig();
  const { records: adrs, graph } = await getAdrData(cfg.projectRoot);

  return (
    <section className="page-card">
      <header className="page-intro">
        <div>
          <p className="eyebrow">Decision record</p>
          <h2>ADRs</h2>
          <p>
            Finalized and draft architecture decisions rendered directly from the
            canonical Markdown files.{" "}
            <EducationalPopover
              title="Architecture Decision Records"
              body="ADRs capture significant decisions: context, the decision, options considered, consequences. The graph shows supersedes (solid) and re-affirms (dashed) relationships."
              href="rules/swe/adr-conventions.md"
            />
          </p>
        </div>
        <aside>
          <span>Current count</span>
          <strong>{adrs.length} decision surfaces</strong>
        </aside>
      </header>

      {adrs.length === 0 ? (
        <EmptyState
          title="No ADRs found"
          body="Run a pipeline that produces architecture decisions or inspect a project that already has `.ai-state/decisions/` populated."
          producerPath=".ai-state/decisions/"
        />
      ) : (
        <div className="adrs-body">
          {/* ── Relationship graph ──────────────────────────────────────────── */}
          {graph.length > 0 ? (
            <details className="adr-graph-details">
              <summary>ADR relationship graph ({graph.length} nodes)</summary>
              <AdrGraphClient nodes={graph} />
            </details>
          ) : null}

          {/* ── Filtered list ───────────────────────────────────────────────── */}
          <AdrFilterClient records={adrs} />
        </div>
      )}
    </section>
  );
}
