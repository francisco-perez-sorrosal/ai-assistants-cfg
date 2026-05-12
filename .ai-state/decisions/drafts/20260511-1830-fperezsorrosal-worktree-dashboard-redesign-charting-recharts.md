---
id: dec-draft-99429dc4
title: Dashboard charting — adopt recharts via a TrendChart wrapper; parse METRICS_LOG.md / SENTINEL_LOG.md for historical series
status: proposed
category: architectural
date: 2026-05-11
summary: Replace hand-rolled SVG charts with recharts (MIT) wrapped in a generic TrendChart component; parse the append-only log files for historical trend series so charts are not flat when only one report JSON exists. Supersedes the Streamlit-era graphviz+plotly+pyvis stack, already obsoleted by the Next.js rewrite.
tags: [dashboard, charts, recharts, metrics, sentinel, nextjs]
made_by: agent
agent_type: systems-architect
branch: worktree-dashboard-redesign
pipeline_tier: full
supersedes: dec-130
affected_files:
  - dashboard_app/src/components/viz/trend-chart.tsx
  - dashboard_app/src/components/viz/sparkline.tsx
  - dashboard_app/src/components/metrics-dashboard.tsx
  - dashboard_app/src/server/view-models/metrics.ts
  - dashboard_app/src/server/view-models/sentinel.ts
  - dashboard_app/src/lib/metrics.ts
  - dashboard_app/package.json
---

## Context

`dashboard_app/`'s metrics charts are hand-rolled SVG line charts (720×280 viewBox, fixed grid, `<title>`-only tooltips) — no hover crosshair, no zoom, no responsive breakpoints, no real interactivity. The sentinel page has no chart at all (the Streamlit reference had a Plotly health-grade sparkline). There is also a data gap: the dashboard reads per-snapshot `METRICS_REPORT_*.json` files for trend history, whereas the Streamlit reference read `METRICS_LOG.md` aggregates — so if only the latest JSON exists, the dashboard's trends are flat.

dec-130 ("Pipeline Dashboard visualization stack — graphviz + plotly + pyvis (lazy)") chose those libraries for the *Streamlit* runtime, which dec-134 replaced wholesale. The Streamlit dashboard no longer exists as the active runtime; dec-130 is de-facto obsolete.

Activation: yes — technology selection (new dep); supersedes a prior ADR.

## Decision

Adopt **`recharts`** (MIT, React-19/Next-16 compatible, widely used, good built-in crosshair/tooltip/responsive) for all line charts. Wrap it in a generic `TrendChart` component (`{ series: {label, color, points: {x, y|null}[]}[], xLabel?, yFormatter?, height? }`) so the rest of the app never touches recharts APIs — a single swap point if the lib ever changes. `Sparkline` is a thin `TrendChart` preset (no axes, single series, color-by-value). Both live in `dashboard_app/src/components/viz/` and contain zero metric-name / grade-alphabet hardcoding — that all comes from props.

For the historical-trend gap: add `parseMetricsLog(body)` to the metrics view-model — when `METRICS_LOG.md` is present, its append-only aggregate rows are the trend series; otherwise fall back to per-JSON-snapshot history. Same pattern for the sentinel page: `parseSentinelLog(body)` from `SENTINEL_LOG.md` feeds the health-grade sparkline. The would-be-dead `parseMarkdownTable` (slated for removal after Sentrux excision) gets reused for `parseMetricsLog`.

dec-130 is **superseded**: the graphviz/plotly/pyvis stack belonged to the Streamlit runtime; under Next.js, charts are recharts (line charts) and the ADR/step graphs are pure SVG (sibling ADR) — no Graphviz binary dependency, no pyvis.

Plotly.js is *not* adopted despite matching the old static-viewer look — it is ~3 MB and a heavyweight imperative API; bundle size is a soft concern for a per-user local Node app but Plotly's cost is unjustified for line charts. `recharts` (~100 KB gz) is the lowest-friction maintained choice.

## Considered Options

### A — Keep hand-rolled SVG, add crosshair/tooltip by hand

Pros: zero new dep. Cons: ~150 LOC of fiddly crosshair/tooltip/responsive math to write and maintain; reinventing recharts. Rejected.

### B — recharts (chosen)

Pros: declarative, SSR-friendly inside an existing `"use client"` boundary, good interactivity out of the box, isolated behind `TrendChart`. Cons: one new client dep; recharts SSR needs the chart in a client boundary (already true). Accepted.

### C — Visx

Pros: lower-level, flexible. Cons: more code to assemble basic line+tooltip; not worth it over recharts. Rejected.

### D — Plotly.js

Pros: matches the old Streamlit / static-viewer aesthetic. Cons: ~3 MB; heavyweight imperative API; overkill for line charts. Rejected.

## Consequences

**Positive:** Real interactive charts (crosshair, tooltip, responsive) with little code; the sentinel page gets its health sparkline; trends are no longer flat when only one report JSON exists; `parseMarkdownTable` is reused instead of deleted; dec-130's Streamlit-era stack is retired cleanly.

**Negative:** One new client dep; pin the recharts version (major-version churn is isolated by the `TrendChart` wrapper).

**Risks accepted:** recharts `ResponsiveContainer` can render width=0 on first paint / hydration mismatch — mitigated by a fixed `height` + `width="100%"` and the chart already living in a `"use client"` boundary.

## Prior Decision

dec-130 selected `st.graphviz_chart` + `plotly` + `pyvis` (lazy) for the Streamlit dashboard's five visualization needs (step DAGs, REQ→test bipartite, ADR lineage, file-overlap heatmap, architecture SVG embed). dec-134 then replaced the Streamlit runtime with Next.js, making the Streamlit-bound library choices obsolete. Under Next.js: line charts → recharts (this ADR); ADR lineage + step DAG → pure SVG (sibling ADR `adr-graph-pure-svg`); architecture SVG → the diagram-serving route + pan/zoom viewer (sibling ADR); the bipartite and heatmap views were dashboard-internal-only and are not carried into v1 (deferred — see SYSTEMS_PLAN). This ADR supersedes dec-130 on the line-chart axis; the graph-axis supersession is recorded in `adr-graph-pure-svg`. Re-opening (e.g., to add Plotly back for visual parity with the legacy static viewer) would require a concrete demand signal and acceptance of Plotly's ~3 MB cost.
