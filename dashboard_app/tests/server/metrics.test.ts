import { mkdir, mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { afterEach, describe, expect, it } from "vitest";

import { type DashboardMetricsData, formatMetricDelta, getMetricTone, sliceLogSeriesUpTo, sliceSnapshotsUpTo } from "@/lib/metrics";
import type { MetricsLogPoint } from "@/lib/metrics";
import { getMetricsData } from "@/server/view-models/metrics";

describe("metrics dashboard data", () => {
  it("keeps pure metric helper behavior stable for dashboard selection and tone cues", () => {
    const snapshots = [
      { id: "first" },
      { id: "second" },
      { id: "third" }
    ] as Array<{ id: string }>;

    expect(sliceSnapshotsUpTo(snapshots, "second").map((snapshot) => snapshot.id)).toEqual([
      "first",
      "second"
    ]);
    expect(getMetricTone("coverage_line_pct", 0.02)).toBe("good");
    expect(getMetricTone("hotspot_top_score", 20)).toBe("bad");
    expect(formatMetricDelta("coverage_line_pct", 0.015)).toBe("+1.5 pts");
  });
});

function makeLogPoint(timestamp: string | null): MetricsLogPoint {
  return {
    timestamp,
    commit_sha: null,
    window_days: null,
    sloc_total: null,
    file_count: null,
    language_count: null,
    ccn_p95: null,
    cognitive_p95: null,
    cyclic_deps: null,
    churn_total_90d: null,
    change_entropy_90d: null,
    truck_factor: null,
    hotspot_top_score: null,
    hotspot_gini: null,
    coverage_line_pct: null,
    report_file: null
  };
}

describe("sliceLogSeriesUpTo", () => {
  const rows = [
    makeLogPoint("2026-01-01T00:00:00Z"),
    makeLogPoint("2026-02-01T00:00:00Z"),
    makeLogPoint("2026-03-01T00:00:00Z"),
    makeLogPoint("2026-04-01T00:00:00Z")
  ];

  it("returns all rows when untilTimestamp is null", () => {
    expect(sliceLogSeriesUpTo(rows, null)).toHaveLength(4);
  });

  it("returns only rows at or before the given timestamp", () => {
    const result = sliceLogSeriesUpTo(rows, "2026-02-01T00:00:00Z");
    expect(result).toHaveLength(2);
    expect(result[0]?.timestamp).toBe("2026-01-01T00:00:00Z");
    expect(result[1]?.timestamp).toBe("2026-02-01T00:00:00Z");
  });

  it("returns empty array when timestamp is before all rows", () => {
    const result = sliceLogSeriesUpTo(rows, "2025-12-31T23:59:59Z");
    expect(result).toHaveLength(0);
  });

  it("drops rows with null timestamps when filtering", () => {
    const rowsWithNull = [
      makeLogPoint(null),
      makeLogPoint("2026-02-01T00:00:00Z"),
      makeLogPoint("2026-03-01T00:00:00Z")
    ];
    const result = sliceLogSeriesUpTo(rowsWithNull, "2026-02-15T00:00:00Z");
    expect(result).toHaveLength(1);
    expect(result[0]?.timestamp).toBe("2026-02-01T00:00:00Z");
  });
});

const tempRoots: string[] = [];

async function createTempProjectRoot(prefix: string): Promise<string> {
  const root = await mkdtemp(path.join(os.tmpdir(), prefix));
  tempRoots.push(root);
  return root;
}

afterEach(async () => {
  await Promise.all(tempRoots.splice(0).map((root) => rm(root, { force: true, recursive: true })));
});

describe("Sentrux excision — metrics view-model", () => {
  it("getMetricsData result has no sentrux key at runtime", async () => {
    const root = await createTempProjectRoot("metrics-sentrux-test-");
    await mkdir(path.join(root, ".ai-state", "metrics_reports"), { recursive: true });

    const result = await getMetricsData(root);

    expect(Object.keys(result)).not.toContain("sentrux");
  });

  it("DashboardMetricsData type has no sentrux property at compile time", () => {
    const data: DashboardMetricsData = {
      latest: null,
      latestPath: null,
      log: null,
      logSeries: [],
      snapshots: []
    };

    // Negative compile-time assertion: accessing .sentrux must be a type error.
    // @ts-expect-error — sentrux was removed from DashboardMetricsData; this line must not typecheck.
    const _unused = data.sentrux;
    void _unused;

    expect(Object.keys(data)).not.toContain("sentrux");
  });
});
