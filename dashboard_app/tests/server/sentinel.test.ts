import { describe, expect, it } from "vitest";

import { parseMetricsLog } from "@/server/view-models/metrics";
import { extractSections, parseSentinelLog } from "@/server/sentinel/extract-sections";

// ---------------------------------------------------------------------------
// extractSections
// ---------------------------------------------------------------------------

describe("extractSections", () => {
  // Mirrors the real sentinel report structure: preamble sections precede Findings,
  // and additional sections follow after the Suggested block (terminated by a ## heading).
  const FIXTURE_BODY = `
## Ecosystem Health: B

### Summary

Preamble text here.

---

## Metrics

| Metric | Value |
|--------|-------|
| Skills | 42    |

---

## Findings

### Critical (blocks correct behavior)

*None.*

### Important (degrades quality or efficiency)

| # | Check | Finding |
|---|-------|---------|
| I1 | AC07 | Some important finding |

### Suggested (improves but not urgent)

| # | Check | Finding |
|---|-------|---------|
| S1 | F07 | Some suggested finding |

---

## Pipeline Discipline

Post-finding content here.
`.trim();

  it("extracts all three sections from a complete report body", () => {
    const result = extractSections(FIXTURE_BODY);

    expect(result.critical).toContain("Critical");
    expect(result.critical).toContain("*None.*");

    expect(result.important).toContain("Important");
    expect(result.important).toContain("AC07");

    expect(result.suggested).toContain("Suggested");
    expect(result.suggested).toContain("F07");
  });

  it("rest excludes the three sections but includes preamble and other sections", () => {
    const result = extractSections(FIXTURE_BODY);

    expect(result.rest).toContain("Preamble text here.");
    expect(result.rest).toContain("## Metrics");
    expect(result.rest).toContain("## Pipeline Discipline");
    expect(result.rest).toContain("Post-finding content here.");

    expect(result.rest).not.toContain("*None.*");
    expect(result.rest).not.toContain("AC07");
    expect(result.rest).not.toContain("F07");
  });

  it("returns empty string for a missing section", () => {
    const bodyWithoutSuggested = `
### Critical (blocks correct behavior)

*None.*

### Important (degrades quality or efficiency)

Some important text.
`.trim();

    const result = extractSections(bodyWithoutSuggested);

    expect(result.suggested).toBe("");
    expect(result.critical).toContain("Critical");
    expect(result.important).toContain("Important");
  });

  it("rest contains the full body when no finding sections are present", () => {
    const bodyNoSections = "## Overview\n\nJust a summary.\n";

    const result = extractSections(bodyNoSections);

    expect(result.critical).toBe("");
    expect(result.important).toBe("");
    expect(result.suggested).toBe("");
    expect(result.rest).toContain("Just a summary.");
  });

  it("matching is case-insensitive for section headings", () => {
    const body = "### CRITICAL (blocks correct behavior)\n\nFound critical.\n### important\n\nFound important.\n";

    const result = extractSections(body);

    expect(result.critical).toContain("Found critical.");
    expect(result.important).toContain("Found important.");
  });
});

// ---------------------------------------------------------------------------
// parseSentinelLog
// ---------------------------------------------------------------------------

describe("parseSentinelLog", () => {
  const FIXTURE_LOG = `
# Sentinel Log

| Timestamp            | Health Grade | Artifacts | Findings (C/I/S) | Ecosystem Coherence | Report File                              |
|----------------------|--------------|-----------|-------------------|---------------------|------------------------------------------|
| 2026-02-08T14:30:00Z | B            | 31        | 0/5/6             | B                   | SENTINEL_REPORT_2026-02-08_14-30-00.md   |
| 2026-03-16T11:02:14Z | A            | 47        | 0/0/5             | A                   | SENTINEL_REPORT_2026-03-16_11-02-14.md   |
| 2026-03-20T01:19:06Z | B            | 49        | 1/3/6             | A                   | SENTINEL_REPORT_2026-03-20_01-19-06.md   |
`.trim();

  it("parses a well-formed log table into typed SentinelLogPoint array", () => {
    const result = parseSentinelLog(FIXTURE_LOG);

    expect(result).toHaveLength(3);

    const first = result[0];
    expect(first?.timestamp).toBe("2026-02-08T14:30:00Z");
    expect(first?.grade).toBe("B");
    expect(first?.critical).toBe(0);
    expect(first?.important).toBe(5);
    expect(first?.suggested).toBe(6);
    expect(first?.coherence).toBe("B");
  });

  it("parses a row with non-zero critical count", () => {
    const result = parseSentinelLog(FIXTURE_LOG);

    const withCritical = result[2];
    expect(withCritical?.critical).toBe(1);
    expect(withCritical?.important).toBe(3);
    expect(withCritical?.suggested).toBe(6);
    expect(withCritical?.coherence).toBe("A");
  });

  it("returns an empty array for an empty or headerless body", () => {
    expect(parseSentinelLog("")).toHaveLength(0);
    expect(parseSentinelLog("# Title\n\nNo table here.")).toHaveLength(0);
  });

  it("coerces missing or garbage cells to null", () => {
    const logWithGarbage = `
| Timestamp | Health Grade | Artifacts | Findings (C/I/S) | Ecosystem Coherence | Report File |
|-----------|--------------|-----------|-------------------|---------------------|-------------|
| 2026-05-01T00:00:00Z |  | 30 | not/a/number | B | REPORT.md |
`.trim();

    const result = parseSentinelLog(logWithGarbage);

    expect(result).toHaveLength(1);
    const row = result[0];
    expect(row?.grade).toBeNull();
    expect(row?.critical).toBeNull();
    expect(row?.important).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// parseMetricsLog
// ---------------------------------------------------------------------------

describe("parseMetricsLog", () => {
  const FIXTURE_LOG = `
| schema_version | timestamp | commit_sha | window_days | sloc_total | file_count | language_count | ccn_p95 | cognitive_p95 | cyclic_deps | churn_total_90d | change_entropy_90d | truck_factor | hotspot_top_score | hotspot_gini | coverage_line_pct | report_file |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.0.0 | 2026-04-24T23:22:44.289638+00:00 | ee61f06c | 30 | 83355 | 510 | 13 | 8.0 | 10.0 | 0 | 95101 | 319.93 | 1 | 58023.0 | 0.6802 | 0.7986 | [METRICS_REPORT_2026-04-24_23-22-51.md](METRICS_REPORT_2026-04-24_23-22-51.md) |
| 1.0.0 | 2026-05-09T06:07:59.311418+00:00 | 912ee1ae | 30 | 108725 | 679 | 15 | 8.0 | 9.0 | 0 | 98081 | 255.81 | 1 | 21399.0 | 0.6224 | 0.5408 | [METRICS_REPORT_2026-05-09_06-08-07.md](METRICS_REPORT_2026-05-09_06-08-07.md) |
`.trim();

  it("parses a well-formed log table into typed MetricsLogPoint array", () => {
    const result = parseMetricsLog(FIXTURE_LOG);

    expect(result).toHaveLength(2);

    const first = result[0];
    expect(first?.timestamp).toBe("2026-04-24T23:22:44.289638+00:00");
    expect(first?.sloc_total).toBe(83355);
    expect(first?.file_count).toBe(510);
    expect(first?.language_count).toBe(13);
    expect(first?.ccn_p95).toBe(8.0);
    expect(first?.coverage_line_pct).toBe(0.7986);
    expect(first?.cyclic_deps).toBe(0);
    expect(first?.truck_factor).toBe(1);
  });

  it("strips markdown link syntax from report_file cell", () => {
    const result = parseMetricsLog(FIXTURE_LOG);

    expect(result[0]?.report_file).toBe("METRICS_REPORT_2026-04-24_23-22-51.md");
    expect(result[1]?.report_file).toBe("METRICS_REPORT_2026-05-09_06-08-07.md");
  });

  it("coerces blank or non-numeric cells to null", () => {
    const logWithGaps = `
| schema_version | timestamp | commit_sha | window_days | sloc_total | file_count | language_count | ccn_p95 | cognitive_p95 | cyclic_deps | churn_total_90d | change_entropy_90d | truck_factor | hotspot_top_score | hotspot_gini | coverage_line_pct | report_file |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.0.0 |  | abc | not-a-number | | 100 | | 5.0 | | 0 | | | 1 | | | | |
`.trim();

    const result = parseMetricsLog(logWithGaps);

    expect(result).toHaveLength(1);
    const row = result[0];
    expect(row?.timestamp).toBeNull();
    expect(row?.window_days).toBeNull();
    expect(row?.sloc_total).toBeNull();
    expect(row?.file_count).toBe(100);
    expect(row?.language_count).toBeNull();
    expect(row?.ccn_p95).toBe(5.0);
  });

  it("returns an empty array for an empty or headerless body", () => {
    expect(parseMetricsLog("")).toHaveLength(0);
    expect(parseMetricsLog("# Title\n\nNo table.")).toHaveLength(0);
  });
});
