import { EducationalPopover } from "@/components/educational-popover";
import { EmptyState } from "@/components/empty-state";
import { PageShell } from "@/components/page-shell";
import { getConfig } from "@/lib/config";
import { getSentinelData } from "@/server/view-models/sentinel";
import type { SentinelLogPoint } from "@/server/view-models/sentinel";

import { SentinelClient } from "./sentinel-client";
import { SentinelSparklineClient } from "./sentinel-sparkline-client";

// ─── Grade helpers ────────────────────────────────────────────────────────────

const GRADE_NUMBERS: Record<string, number> = {
  a: 4,
  b: 3,
  c: 2,
  d: 1
};

function gradeToNumber(grade: string | null): number | null {
  if (grade === null) {
    return null;
  }
  return GRADE_NUMBERS[grade.toLowerCase()] ?? null;
}

function logSeriesToSparklinePoints(
  logSeries: SentinelLogPoint[]
): Array<{ x: string; y: number | null }> {
  return logSeries.map((point, idx) => ({
    x: point.timestamp ?? String(idx + 1),
    y: gradeToNumber(point.grade)
  }));
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default async function SentinelPage() {
  const cfg = getConfig();
  const sentinel = await getSentinelData(cfg.projectRoot);

  const sources = (
    <>
      <p>
        Reads <code>.ai-state/sentinel_reports/</code> — timestamped audit reports and
        the <code>SENTINEL_LOG.md</code> run summary.
      </p>
      <p>
        Reports found: <strong>{sentinel.reports.length}</strong>
      </p>
    </>
  );

  return (
    <PageShell title="Sentinel" sourcesContent={sources}>
      <p className="page-intro__lede muted">
        Health history and per-report audits rendered from{" "}
        <code>.ai-state/sentinel_reports/</code>.{" "}
        <EducationalPopover
          title="Sentinel audits"
          body="The sentinel agent audits the project's context artifacts across ten dimensions and grades overall health. Findings are tiered Critical / Important / Suggested."
          href="agents/sentinel.md"
        />
      </p>

      {sentinel.reports.length === 0 ? (
        <EmptyState
          title="No sentinel reports found"
          body="Run `/sentinel` in the target project to generate the first ecosystem audit."
          producerPath=".ai-state/sentinel_reports/"
        />
      ) : (
        <div className="sentinel-body">
          {sentinel.logSeries.length > 0 ? (
            <div className="sentinel-sparkline-row">
              <span className="sentinel-sparkline-label muted">Health grade trend</span>
              <SentinelSparklineClient
                points={logSeriesToSparklinePoints(sentinel.logSeries)}
              />
            </div>
          ) : null}

          <SentinelClient reports={sentinel.reports} />
        </div>
      )}
    </PageShell>
  );
}
