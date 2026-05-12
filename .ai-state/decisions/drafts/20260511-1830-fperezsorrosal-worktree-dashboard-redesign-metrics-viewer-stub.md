---
id: dec-draft-d9e81c5a
title: Replace metrics-viewer.html.tmpl with a static redirect stub; remove the committed index.html and orphaned SENTRUX_* files
status: proposed
category: architectural
date: 2026-05-11
summary: The dashboard now fully covers the Chart.js metrics viewer (and adds interactivity + the sentinel sparkline). Replace metrics-viewer.html.tmpl with a ~30-line static stub pointing at the dashboard, keep deploying it via /onboard-project Phase 4 so bookmarks resolve, and delete Praxion's own .ai-state/metrics_reports/index.html plus the orphaned SENTRUX_* files. Supersedes the soft-deprecation-with-banner plan.
tags: [dashboard, metrics-viewer, onboarding, sentrux, deprecation, supersession]
made_by: agent
agent_type: systems-architect
branch: worktree-dashboard-redesign
pipeline_tier: full
supersedes: dec-129
affected_files:
  - claude/aac-templates/metrics-viewer.html.tmpl
  - commands/onboard-project.md
  - .ai-state/metrics_reports/index.html
---

## Context

`claude/aac-templates/metrics-viewer.html.tmpl` is a static HTML + Chart.js viewer for `/project-metrics` data, byte-identically deployed into onboarded projects as `.ai-state/metrics_reports/index.html` (via `/onboard-project` Phase 4). It carries 28 Sentrux references (`SENTRUX_COLUMNS`, `SENTRUX_KPIS`, `SENTRUX_PANELS`, references to `scripts/sentrux_history.py` and `skills/sentrux/SKILL.md`) — Sentrux was removed wholesale on 2026-05-08 (`td-016`), so every project that onboards from here gets a copy with dead Sentrux UI. dec-129 declared the template "soft-deprecated, hard removal in the next release" with a deprecation banner. The dashboard's Metrics page now reproduces every property of the static viewer (KPI grid, trend lines, hotspot table) *and* adds what it can't do (auto-refresh, educational popovers, the sentinel health sparkline, the ADR graph). Praxion's own repo also carries `.ai-state/metrics_reports/index.html` — a committed HTML file with no MD source bearing `share_out: true`, which violates `html-output-conventions.md`.

Activation: yes — changes the onboarding contract; supersedes a prior ADR.

## Decision

Replace `claude/aac-templates/metrics-viewer.html.tmpl` with a **minimal (~30-line) static HTML stub**: a single card reading *"The interactive metrics viewer has moved. Run `praxion-dashboard start <project>` (or `/dashboard`) and open the Metrics tab. This file is retained as a pointer only — the `METRICS_REPORT_*.md` files in this directory contain the raw metrics for offline reading."* with links to the sibling `METRICS_REPORT_*.md` files. `/onboard-project` Phase 4 **keeps deploying this stub** (so a user who bookmarked `.ai-state/metrics_reports/index.html` still resolves to something useful). In **Praxion's own repo**, delete `.ai-state/metrics_reports/index.html` (the convention-violating committed HTML), `.ai-state/metrics_reports/SENTRUX_HISTORY.md`, and `.ai-state/metrics_reports/SENTRUX_REPORT_2026-05-05_03-43-48.{json,md}` (orphaned — no producer remains; already flagged by a sentinel S3 finding).

dec-129 is **superseded**: instead of repairing the Chart.js viewer + adding a banner over one release cycle, the template becomes a permanent pointer-stub now. Repairing the Chart.js machinery would mean maintaining a parallel metrics renderer indefinitely — exactly the dual-source-of-truth dec-129 wanted gone. Removing the template *entirely* (no stub) would break the bookmark; the stub is the gentlest path that still eliminates the Sentrux residue (by deleting the whole Chart.js machinery).

## Considered Options

### A — Repair the template (strip the 28 Sentrux refs, keep it as an offline Chart.js fallback)

Pros: truly-offline metrics trends survive. Cons: maintains a parallel metrics renderer forever — the dual-source-of-truth dec-129 explicitly wanted to retire; the Chart.js code is ~700 lines to keep in sync with the metrics schema. Rejected.

### B — Replace with a static redirect stub (chosen)

Pros: no parallel renderer to maintain; bookmarks resolve to a helpful pointer + the MD reports; the Sentrux refs are gone by deletion of the whole Chart.js machinery; Praxion's repo stops carrying a convention-violating HTML file. Cons: truly-offline metrics viewing is reduced to reading `METRICS_REPORT_*.md` (already generated per run) — acceptable. Accepted.

### C — Remove the template from onboarding entirely

Pros: cleanest. Cons: a user who bookmarked `.ai-state/metrics_reports/index.html` gets a 404. Rejected — the stub costs ~30 lines and preserves the bookmark.

## Consequences

**Positive:** No parallel metrics renderer; bookmarks resolve helpfully; the 28 Sentrux refs in the shipped template are gone; Praxion's repo no longer carries a `html-output-conventions.md`-violating committed HTML; `td-016` Sentrux excision finally reaches the onboarding template.

**Negative:** Offline metrics viewing without a running dashboard is reduced to reading the MD reports — mitigated by the stub linking them and by the dashboard being one command away.

**Risks accepted:** A user who relied on the Chart.js trends offline loses them — acceptable; flagged in the CHANGELOG. The stub-deployment step in `/onboard-project` Phase 4 must be updated to copy the stub (not the old template).

## Prior Decision

dec-129 chose "soft deprecation over one release cycle": v1 ships both viewers; the static viewer gains a deprecation banner; the next release deletes `metrics-viewer.html.tmpl` and the Phase-2 deploy step. That plan assumed the static viewer would be *repaired and banner-ed* during the window — but it still carries Sentrux residue, and the dashboard now fully covers it. Rather than repair-then-delete-later, this ADR jumps to the end state now (the template becomes a permanent pointer-stub, the bookmark survives), with the Sentrux residue eliminated by deleting the Chart.js machinery wholesale. Re-opening (e.g., to bring back an offline Chart.js viewer) would require a concrete demand signal for dashboard-less offline metrics trends that the per-run MD reports don't satisfy.
