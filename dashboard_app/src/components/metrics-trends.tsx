"use client";

import { TrendChart } from "@/components/viz/trend-chart";
import type { TrendSeries } from "@/components/viz/trend-chart";
import { EducationalPopover } from "@/components/educational-popover";
import type {
  MetricChartSection,
  MetricKey,
  MetricsLogPoint,
  MetricsSnapshot
} from "@/lib/metrics";
import {
  formatChartAxisValue,
  formatMetricValue,
  formatSnapshotLabel,
  getMetricDirectionCopy,
  METRIC_CHART_SECTIONS,
  METRIC_DEFINITIONS
} from "@/lib/metrics";

// ─── Series builders ──────────────────────────────────────────────────────────

const CHART_HEIGHT = 220;

/**
 * Builds a TrendSeries per metric key from METRICS_LOG.md rows.
 * x is the log row timestamp (truncated to date for readability).
 * Rows where the metric value is null are skipped (recharts renders gaps).
 */
function seriesFromLog(
  logSeries: MetricsLogPoint[],
  metricKey: MetricKey
): TrendSeries {
  const definition = METRIC_DEFINITIONS[metricKey];
  const points = logSeries.flatMap((row) => {
    const y = row[metricKey];
    if (y === null) return [];
    const x = row.timestamp
      ? row.timestamp.slice(0, 10)
      : row.report_file ?? "?";
    return [{ x, y }];
  });
  return { color: definition.chartColor, label: definition.shortLabel, points };
}

/**
 * Builds a TrendSeries per metric key from MetricsSnapshot[].
 * Fallback path when METRICS_LOG.md has no rows.
 */
function seriesFromSnapshots(
  snapshots: MetricsSnapshot[],
  metricKey: MetricKey
): TrendSeries {
  const definition = METRIC_DEFINITIONS[metricKey];
  const points = snapshots.flatMap((snapshot) => {
    const y = snapshot.aggregate[metricKey];
    if (y === null) return [];
    return [{ x: formatSnapshotLabel(snapshot.aggregate.timestamp), y }];
  });
  return { color: definition.chartColor, label: definition.shortLabel, points };
}

function buildSectionSeries(
  section: MetricChartSection,
  snapshots: MetricsSnapshot[],
  logSeries: MetricsLogPoint[]
): TrendSeries[] {
  const useLog = logSeries.length > 0;
  return section.metrics.map((metricKey) =>
    useLog
      ? seriesFromLog(logSeries, metricKey)
      : seriesFromSnapshots(snapshots, metricKey)
  );
}

// ─── MetricTrendSection ────────────────────────────────────────────────────────

function MetricTrendSection({
  logSeries,
  section,
  snapshots
}: {
  logSeries: MetricsLogPoint[];
  section: MetricChartSection;
  snapshots: MetricsSnapshot[];
}) {
  const series = buildSectionSeries(section, snapshots, logSeries);
  const hasPoints = series.some((s) => s.points.length > 0);

  return (
    <section className="artifact-card metric-trend-card">
      <div className="metric-trend-card__header">
        <div>
          <h3>{section.title}</h3>
          <p className="muted">{section.note}</p>
        </div>
        <div className="metric-trend-card__hints">
          {section.metrics.map((metricKey) => (
            <EducationalPopover
              key={metricKey}
              body={`${METRIC_DEFINITIONS[metricKey].summary} ${getMetricDirectionCopy(metricKey)}`}
              title={METRIC_DEFINITIONS[metricKey].label}
            />
          ))}
        </div>
      </div>
      {hasPoints ? (
        <TrendChart
          series={series}
          height={CHART_HEIGHT}
          yFormatter={(v) => formatChartAxisValue(v)}
        />
      ) : (
        <p className="muted">Not enough data points yet for this metric group.</p>
      )}
    </section>
  );
}

// ─── MetricsTrends ────────────────────────────────────────────────────────────

export function MetricsTrends({
  logSeries,
  snapshots
}: {
  logSeries: MetricsLogPoint[];
  snapshots: MetricsSnapshot[];
}) {
  return (
    <div className="grid-two">
      {METRIC_CHART_SECTIONS.map((section) => (
        <MetricTrendSection
          key={section.title}
          logSeries={logSeries}
          section={section}
          snapshots={snapshots}
        />
      ))}
    </div>
  );
}
