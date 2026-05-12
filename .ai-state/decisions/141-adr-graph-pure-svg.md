---
id: dec-141
title: ADR relationship graph — pure-SVG layered layout, no graph-layout library
status: accepted
category: architectural
date: 2026-05-11
summary: The ADR relationship graph (and the workshop step DAG, its single-chain case) is rendered as pure SVG with a hand-rolled longest-path layering computed in useMemo; no dagre / elkjs / d3 dependency. Supersedes the deferred-Mermaid decision, which is moot under the new diagram pipeline.
tags: [dashboard, adr, visualization, graph, svg, nextjs]
made_by: agent
agent_type: systems-architect
branch: worktree-dashboard-redesign
pipeline_tier: full
supersedes: dec-125
affected_files:
  - dashboard_app/src/components/viz/decision-graph.tsx
  - dashboard_app/src/server/view-models/adr-graph.ts
  - dashboard_app/src/server/view-models/adrs.ts
  - dashboard_app/src/app/adrs/page.tsx
  - dashboard_app/src/app/workshops/page.tsx
---

## Context

The ADRs page has no relationship visualization; the Streamlit reference used graphviz DOT (server-side render, requires a Graphviz binary). The redesign wants a generic interactive node-link graph from ADR frontmatter (`supersedes`/`superseded_by`/`re_affirms`/`re_affirmed_by`) + `DECISIONS_INDEX.md` — node color by `status`, solid edges for supersession, dashed for re-affirmation, click-to-expand — usable against any Praxion project's ADR set (typically 10–150 nodes). The same need recurs for the workshop step DAG (Streamlit had it; the Next.js app doesn't).

dec-125 ("Pipeline Dashboard Mermaid rendering — defer to v2") was scoped to the Streamlit runtime, which dec-134 replaced wholesale; and the new diagram-serving pipeline (sibling ADR) renders every diagram class Praxion actually emits (LikeC4 SVGs, and any Mermaid-in-ADR that follows the source/render convention produces an SVG the diagram route serves). So "Mermaid is deferred" is no longer the operative state.

Activation: yes — visualization-stack technology choice; supersedes a prior ADR.

## Decision

Render the ADR relationship graph as **pure SVG** with a **hand-rolled longest-path layering** (Sugiyama-lite): each node's layer = longest supersession-chain depth; nodes are spread within their layer; edges are `<line>` (solid for supersedes/superseded_by, dashed for re_affirms/re_affirmed_by); nodes are `<circle>` colored by `status` (accepted / superseded / proposed / re-affirmation); labels are truncated `<text>` with the full title in `<title>`. The layout is computed once per `nodes` change in a `useMemo` (O(V+E) — sub-millisecond at ~150 nodes); the SVG is wrapped in the shared `usePanZoom` viewport (from the diagram-serving ADR). The graph is interactive (pan / zoom / click-to-expand) but not draggable-rearrangeable. With zero supersession edges present (the common case — most ADRs have no links), the component shows a legend plus a "+N standalone decisions" note rather than a wall of isolated dots; consider rendering only nodes that participate in ≥ 1 edge.

The component's props are the contract: `{ nodes: AdrGraphNode[], onSelect?: (id) => void, minZoom?, maxZoom? }` where `AdrGraphNode = { id; title; status; supersedes?; superseded_by?; re_affirms?; re_affirmed_by? }`. The page owns the "expand the card" behavior via `onSelect`, keeping the component project-agnostic. The same layout primitive renders the workshop step DAG (the single-chain special case: `Step N → Step N+1`, node state done/current/pending).

dec-125 is **superseded**: Mermaid is no longer "deferred" — the new diagram pipeline handles Praxion's diagram classes; a project authoring Mermaid in an ADR body gets an SVG via the source/render convention, served by the diagram route.

## Considered Options

### A — `dagre` + custom SVG render

Pros: solid layered layout. Cons: `dagre` is effectively unmaintained; ~30 KB; the layout it gives for shallow supersession trees isn't visibly better than a hand-rolled layering. Rejected.

### B — `elkjs`

Pros: excellent layouts, well-maintained. Cons: ~500 KB, runs a worker — wildly overkill for ≤ 150 nodes; the layout-as-`useMemo` is swappable for ELK later without changing the component's props if a dense graph ever appears. Rejected for v1.

### C — D3-force

Pros: small-ish (~80 KB). Cons: force layouts look messy for DAGs; non-deterministic (bad for screenshots). Rejected.

### D — Pure SVG, hand-rolled layered layout (chosen)

Pros: zero new dep; deterministic layout (stable across renders, good for screenshots); fully generic; small code (~60 LOC layout + ~80 LOC render); the same primitive powers the workshop step DAG. Cons: layouts won't be as pretty as ELK's for pathological cross-edge-heavy graphs — acceptable for supersession chains, and ELK is a drop-in later. Accepted.

## Consequences

**Positive:** No graph-layout dependency; deterministic, screenshot-friendly layout; the component accepts any ADR-shaped data with zero Praxion-specific logic; the step DAG reuses it for free; dec-125's Mermaid-deferral state is retired cleanly.

**Negative:** A project with a genuinely dense supersession graph (many cross-edges) gets a less-pretty layout — mitigated by pan/zoom, edge-participating-nodes-only filtering, and ELK-swappability behind the stable prop shape.

**Risks accepted:** > 200 nodes might crowd visually — pan/zoom + the standalone-decisions note keep it from looking broken.

## Prior Decision

dec-125 deferred Mermaid rendering to a hypothetical v2, on the basis that Praxion's pipeline emitted zero Mermaid and the only diagram class in use (LikeC4 SVGs) was covered. That decision was made for the *Streamlit* runtime, which dec-134 replaced. Under the new Next.js runtime and the sibling diagram-serving ADR, every diagram class Praxion emits is rendered (LikeC4-generated SVGs are served + pan/zoom-viewed; any Mermaid-in-ADR that follows the source/render convention produces a `rendered/*.svg` the diagram route serves). "Mermaid deferred to v2" is therefore moot; this ADR supersedes it. Re-opening would require Praxion's pipeline to start emitting inline ` ```mermaid ` blocks in committed docs — which the diagram-conventions rule forbids — so no future supersession of *this* decision is anticipated on that axis.
