---
id: dec-125
title: Pipeline Dashboard Mermaid rendering — defer to v2
status: superseded
superseded_by: dec-141
category: architectural
date: 2026-05-07
summary: v1 ships without Mermaid rendering; LikeC4-generated SVGs cover all current architecture diagram needs; v2 reassesses based on demand and on streamlit-mermaid-interactive's maintenance trajectory.
tags: [dashboard, mermaid, v1-scope, deferred, simplicity]
made_by: agent
agent_type: systems-architect
pipeline_tier: full
affected_files:
  - streamlit_app/widgets/graph.py
affected_reqs: [REQ-03]
---

## Context

The research finding flagged three Mermaid options: `streamlit-mermaid` (stale, last release 2022), `streamlit-mermaid-interactive` (v0.1.12, Nov 2025, actively maintained), and `streamlit-markdown` (a unified renderer). The `mmdc` Node.js CLI fallback was also discussed.

Three forcing functions to evaluate:

1. **What Mermaid does Praxion's pipeline actually emit?** Surveying the artifact catalog: ADRs are pure prose; specs are tables; sentinel reports use Markdown tables and prose; metrics reports are JSON+MD-tables; LEARNINGS, WIP, IMPLEMENTATION_PLAN — all prose with no Mermaid. The architecture diagram convention pins Mermaid for *non-C4 architectural diagrams*, but Praxion's authored architecture flows through LikeC4 → SVG. Audit of `.ai-state/`: zero Mermaid blocks present today.
2. **Where would Mermaid show up in a dashboard surface?** Only inside hand-authored Markdown bodies in ADR or LEARNINGS sections. Per the diagram-conventions rule, sequence diagrams are valid Mermaid, but in-pipeline use of sequence diagrams is rare.
3. **Is the Node.js fallback safe to assume?** The research finding flagged this risk explicitly. Praxion does not require Node.js as a runtime prerequisite; assuming `mmdc` is installed would be a new install dependency.

## Decision

**v1 ships without Mermaid rendering.** Mermaid code blocks in any rendered Markdown are passed through `st.markdown()` and display as plain code blocks (Streamlit's default behavior). A small visible note next to such blocks ("Mermaid diagram — open the source file to render") sets expectations.

**v2 reassesses** based on:
- Real demand signals (a user requests inline rendering of a Mermaid block in an ADR)
- The maintenance trajectory of `streamlit-mermaid-interactive` (still active in 12 months?)
- Praxion's own use of Mermaid (does it grow beyond the current zero?)

If v2 lands, the preferred path is `streamlit-mermaid-interactive` (pure Python, no Node.js) — gated behind a feature flag in `config.py` that defaults to `False`.

## Considered Options

### Option A — `streamlit-mermaid-interactive` 0.1.12 in v1

**Pros**: Active maintenance; click-event support; pure Python. **Cons**: 0.1.x version → API instability risk; community-maintained; low download counts; locks v1 to a dependency that may go stale; **adds a dep for a use case that does not exist on disk today**.

### Option B — `mmdc` CLI shell-out

**Pros**: First-party Mermaid; great rendering. **Cons**: Adds Node.js + `@mermaid-js/mermaid-cli` as install prereqs — new burden Praxion does not currently impose.

### Option C — `streamlit-markdown` unified renderer

**Pros**: One library covers Markdown + Mermaid + LaTeX. **Cons**: Same 0.x maintenance risk; replaces Streamlit's native `st.markdown` (a regression in test surface); buys Mermaid we do not need.

### Option D — Defer to v2 (chosen)

**Pros**: Simplicity First — the smallest solution that meets the v1 behavior; zero new dep risk; respects the "every dependency must earn its place" principle; no in-pipeline Mermaid exists to render. **Cons**: A user authoring a Mermaid block in an ADR sees plain code in the ADR detail view; mitigation is a per-block hint that opens the source file in their editor.

## Consequences

**Positive**: No 0.x dep in v1; smaller install footprint; one fewer thing to break; respects the Praxion principle "every always-loaded token (and every always-installed dep) must earn its attention share."

**Negative**: Mermaid-authored ADRs render code blocks rather than diagrams. Acceptable because (a) zero such ADRs exist today, (b) the ADR detail view shows the source file path, (c) the architecture page covers the only diagram class Praxion's pipeline actually emits (LikeC4 SVGs).

**Risks accepted**: A user begins authoring Mermaid in ADRs after v1 ships and is disappointed by the unrendered output. Mitigation: feature flag is already in `config.py` so v2 enabling is a one-line change.
