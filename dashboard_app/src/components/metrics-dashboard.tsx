"use client";

import { useState, useTransition } from "react";

import { EducationalPopover } from "@/components/educational-popover";
import { EmptyState } from "@/components/empty-state";
import { MarkdownSurface } from "@/components/markdown-surface";
import { MetricsSummaryCards, summarizeCollector } from "@/components/metrics-summary-cards";
import { MetricsTrends } from "@/components/metrics-trends";
import type { DashboardMetricsData } from "@/lib/metrics";
import {
  formatSnapshotLong,
  sliceLogSeriesUpTo,
  sliceSnapshotsUpTo
} from "@/lib/metrics";

function toJsonPreview(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

export function MetricsDashboard({ data }: { data: DashboardMetricsData }) {
  const defaultSnapshotId = data.latest?.id ?? data.snapshots.at(-1)?.id ?? null;
  const [selectedSnapshotId, setSelectedSnapshotId] = useState<string | null>(defaultSnapshotId);
  const [isPending, startTransition] = useTransition();

  const activeSnapshot =
    data.snapshots.find((snapshot) => snapshot.id === selectedSnapshotId) ??
    data.latest ??
    data.snapshots.at(-1) ??
    null;
  const visibleSnapshots = sliceSnapshotsUpTo(data.snapshots, activeSnapshot?.id ?? null);
  const visibleLogSeries = sliceLogSeriesUpTo(
    data.logSeries,
    activeSnapshot?.aggregate.timestamp ?? null
  );

  return (
    <section className="page-card metrics-page">
      <header className="page-intro">
        <div>
          <p className="eyebrow">Complexity and health</p>
          <h2>Metrics</h2>
          <p>
            Historical project signals rendered directly from `.ai-state/metrics_reports/`
            with snapshot filtering, semantic coloring, and structural-quality overlays.
          </p>
        </div>
        <aside>
          <span>Latest JSON</span>
          <strong>{data.latest?.fileName ?? "None"}</strong>
          <span>History</span>
          <strong>{data.snapshots.length} snapshots</strong>
        </aside>
      </header>

      {data.snapshots.length === 0 ? (
        <EmptyState
          title="No metrics reports found"
          body="Run `/project-metrics` in the target project to generate the first metrics bundle."
          producerPath=".ai-state/metrics_reports/"
        />
      ) : (
        <>
          <div className="metrics-page__direction">
            <EducationalPopover
              body="Metrics trend over time. Lower complexity, fewer hotspots, and stable churn indicate a healthy codebase. Use snapshot filtering to compare before/after changes."
              title="How to read these metrics"
            />
          </div>
          {activeSnapshot ? (
            <>
              <section className="section-card metrics-toolbar">
                <div>
                  <h3>Snapshot focus</h3>
                  <p className="muted">
                    Show every trend up to a specific snapshot so regressions and recoveries are easy to read.
                  </p>
                </div>
                <label className="metrics-toolbar__control">
                  <span>View through snapshot</span>
                  <select
                    aria-label="View metrics through snapshot"
                    value={activeSnapshot.id}
                    onChange={(event) => {
                      const nextSnapshotId = event.target.value;
                      startTransition(() => {
                        setSelectedSnapshotId(nextSnapshotId);
                      });
                    }}
                  >
                    {[...data.snapshots].reverse().map((snapshot) => (
                      <option key={snapshot.id} value={snapshot.id}>
                        {`${formatSnapshotLong(snapshot.aggregate.timestamp)} · ${snapshot.fileName}`}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="artifact-meta">
                  <span className="chip">{activeSnapshot.fileName}</span>
                  <span className="chip">{visibleSnapshots.length} points in view</span>
                  {activeSnapshot.aggregate.windowDays !== null ? (
                    <span className="chip">{activeSnapshot.aggregate.windowDays}d window</span>
                  ) : null}
                  {activeSnapshot.coverageStatus ? (
                    <span className="chip">coverage {activeSnapshot.coverageStatus}</span>
                  ) : null}
                  {isPending ? <span className="pill-note">Updating view…</span> : null}
                </div>
              </section>

              <MetricsSummaryCards snapshot={activeSnapshot} />

              <MetricsTrends
                logSeries={visibleLogSeries}
                snapshots={visibleSnapshots}
              />

              <div className="grid-two">
                <section className="artifact-card">
                  <h3>Hot spots</h3>
                  <p className="muted">
                    Highest-risk files in the selected snapshot. Lower top scores and lower concentration are healthier.
                  </p>
                  {activeSnapshot.hotspots.length === 0 ? (
                    <p className="muted">No hot-spot rows exist in this snapshot.</p>
                  ) : (
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Rank</th>
                          <th>Path</th>
                          <th>Score</th>
                          <th>Churn 90d</th>
                          <th>Complexity</th>
                        </tr>
                      </thead>
                      <tbody>
                        {activeSnapshot.hotspots.slice(0, 10).map((row) => (
                          <tr key={`${row.path}-${row.rank ?? "na"}`}>
                            <td>{row.rank ?? "—"}</td>
                            <td>{row.path}</td>
                            <td>
                              {row.score === null
                                ? "—"
                                : new Intl.NumberFormat("en-US", {
                                    maximumFractionDigits: 0
                                  }).format(row.score)}
                            </td>
                            <td>
                              {row.churn90d === null
                                ? "—"
                                : new Intl.NumberFormat("en-US", {
                                    maximumFractionDigits: 0
                                  }).format(row.churn90d)}
                            </td>
                            <td>{row.complexity === null ? "—" : row.complexity.toFixed(0)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </section>

                <section className="artifact-card">
                  <h3>Collectors</h3>
                  <p className="muted">
                    Per-tool status for the selected snapshot. Missing collectors degrade gracefully but weaken confidence in the affected metrics.
                  </p>
                  {Object.keys(activeSnapshot.toolAvailability).length === 0 ? (
                    <p className="muted">No collector metadata exists in this snapshot.</p>
                  ) : (
                    <ul className="status-list">
                      {Object.entries(activeSnapshot.toolAvailability).map(([tool, details]) => (
                        <li className="status-row status-row--collector" key={tool}>
                          <div>
                            <strong>{tool}</strong>
                            <span className="muted">{summarizeCollector(tool, details)}</span>
                          </div>
                          <span className={`collector-status collector-status--${details.status}`}>
                            {details.status}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              </div>

              <details className="metrics-raw">
                <summary>Open selected snapshot JSON</summary>
                <pre className="code-block">{toJsonPreview(activeSnapshot)}</pre>
              </details>
            </>
          ) : (
            <section className="artifact-card">
              <h3>Metrics snapshots unavailable</h3>
              <p className="muted">
                No canonical metrics snapshots were readable.
              </p>
            </section>
          )}

          {data.log ? (
            <details className="metrics-raw">
              <summary>Open metrics history log</summary>
              <MarkdownSurface body={data.log.body} />
            </details>
          ) : null}
        </>
      )}
    </section>
  );
}
