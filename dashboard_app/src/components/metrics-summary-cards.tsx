"use client";

import { EducationalPopover } from "@/components/educational-popover";
import type {
  MetricTone,
  MetricsSnapshot,
  SummaryMetricKey,
  ToolAvailability
} from "@/lib/metrics";
import {
  formatMetricDelta,
  formatMetricValue,
  getMetricDirectionCopy,
  getMetricTone,
  METRIC_DEFINITIONS,
  SUMMARY_METRICS
} from "@/lib/metrics";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function toneLabel(tone: MetricTone): string {
  if (tone === "good") return "Improving";
  if (tone === "bad") return "Worsening";
  if (tone === "steady") return "Stable";
  return "Informational";
}

export function summarizeCollector(tool: string, details: ToolAvailability): string {
  if (details.status === "available") {
    return details.version ? `version ${details.version}` : "available";
  }
  return details.reason ?? details.hint ?? `${tool} status unavailable`;
}

// ─── SummaryCard ─────────────────────────────────────────────────────────────

function SummaryCard({
  metricKey,
  snapshot
}: {
  metricKey: SummaryMetricKey;
  snapshot: MetricsSnapshot;
}) {
  const definition = METRIC_DEFINITIONS[metricKey];
  const delta = snapshot.deltas[metricKey]?.delta ?? null;
  const tone = getMetricTone(metricKey, delta);
  const deltaLabel = formatMetricDelta(metricKey, delta);

  return (
    <article className={`metric-summary-card tone-${tone} accent-${definition.accent}`}>
      <div className="metric-summary-card__header">
        <div>
          <p>{definition.label}</p>
          <EducationalPopover
            body={`${definition.summary} ${getMetricDirectionCopy(metricKey)}`}
            title={definition.label}
          />
        </div>
        <span className={`metric-summary-card__tone metric-summary-card__tone--${tone}`}>
          {toneLabel(tone)}
        </span>
      </div>
      <p className="metric-summary-card__value">
        {formatMetricValue(metricKey, snapshot.aggregate[metricKey])}
      </p>
      <p className="metric-summary-card__footer">
        {deltaLabel ? `${deltaLabel} vs previous comparable run` : getMetricDirectionCopy(metricKey)}
      </p>
    </article>
  );
}

// ─── MetricsSummaryCards ──────────────────────────────────────────────────────

export function MetricsSummaryCards({ snapshot }: { snapshot: MetricsSnapshot }) {
  return (
    <div className="metrics-summary-grid">
      {SUMMARY_METRICS.map((metricKey) => (
        <SummaryCard key={metricKey} metricKey={metricKey} snapshot={snapshot} />
      ))}
    </div>
  );
}
