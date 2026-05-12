# Architecture Changelog

Append-only history of `DESIGN.md` verification milestones. Each entry summarizes a feature pipeline that updated the architect-facing design-target document. Owned by systems-architect; appended by the implementer/verifier of each feature.

The current "Last verified" pointer in `.ai-state/DESIGN.md` § 1 is a one-liner referencing the most recent entry below; deep history lives here so the architecture doc stays scannable.

---

## 2026-05-12 — dashboard-redesign (Built)

**Pipeline Dashboard** row in § 3 reflects the completed implementation of the full UX redesign of the Next.js runtime (`dashboard_app/`): a CSS-custom-property design-token layer; a hand-rolled pan/zoom **diagram viewer**; a pure-SVG **ADR relationship graph** (status-colored nodes, supersedes/re-affirms edges, click-to-expand) reused as the workshop step DAG (step N supersedes step N-1, forming a connected chain); a `recharts` **trend-chart** wrapper feeding the metrics charts and a new sentinel health sparkline (historical series parsed from `METRICS_LOG.md` / `SENTINEL_LOG.md`); server-side **SVG sanitization** (`sanitize-html`) for any inline-injected SVG; a `GET /api/diagram?path=<rel>` **route handler** streaming allowlisted SVGs (+ server-side markdown image-ref rewriting so DESIGN.md / architecture.md diagrams render; explicit-diagrams scanner now covers both `docs/diagrams/` and `.ai-state/diagrams/`); a typed **renderer registry** (`Map<diataxis|contentType, ReactComponent>`) with `reference`/`explanation`/`default` Diátaxis shells (documentation page dispatches through it); reusable chrome (`ArtifactCard`, enhanced `EmptyState`, `EducationalPopover`, `Chip`, `Tabs`, `ErrorState`); `validateProjectRoot` relaxed to require only `.ai-state/` (fresh projects work) + an actionable error page for missing `PRAXION_PROJECT_ROOT`; full **Sentrux excision** across `dashboard_app/`, the shipped `metrics-viewer.html.tmpl` (now a static redirect stub, still deployed by `/onboard-project` Phase 4), and Praxion's orphaned `.ai-state/metrics_reports/` files; `tsconfig.json` gains `noUncheckedIndexedAccess`; `parseWipBody` accepts a second checklist format. New deps: `sanitize-html`, `recharts`. `ALLOWED_ARTIFACT_ROOTS` exported from single source (`server/artifacts/project-root.ts`); `MetadataChips` renders summary without truncation.

Seven draft ADRs under `.ai-state/decisions/drafts/`: diagram-serving-and-svg-sanitization, adr-graph-pure-svg (supersedes dec-125), charting-recharts (supersedes dec-130), renderer-registry-and-diataxis-shells, metrics-viewer-stub (supersedes dec-129), validate-project-root-relaxation, design-token-layer. `docs/architecture.md` updated.

## 2026-05-07 — pipeline-dashboard (Designed)

New component **Pipeline Dashboard** added to § 3 — Praxion-bundled Streamlit reader with six surfaces (Architecture, Workshops, ADRs, Sentinel, Roadmap, Metrics) reading `.ai-state/` + `.ai-work/<task-slug>/` directly with no new persistence layer. Bash ctl + macOS launchd lifecycle mirroring `phoenix-ctl`; per-project sha256-derived port mirroring `chronograph-ctl`; dedicated `~/.praxion-dashboard/venv/` isolation. macOS-only v1 with documented manual-launch fallback for Linux/Windows. Soft-deprecates `metrics-viewer.html.tmpl` over one release cycle.

Ten draft ADRs under `.ai-state/decisions/drafts/`: process model, port allocation, cross-platform scope, frontmatter parsing, Mermaid deferral, poll interval, dependency isolation, visualization stack, CLAUDE.md placement, metrics-viewer supersession. Implementation deferred to implementation-planner spawn; `docs/architecture.md` not yet updated — Built status pending.

## 2026-05-03 — ai-training-onramp (Designed)

Third project archetype — ML/AI training — added to the catalog with three new components (Project archetype catalog, ML training subsystem, Neo-cloud abstraction), three new interfaces (`training_job_descriptor`, `TRAINING_RESULTS.md`, `program.md`), and three new constraints (descriptor mode-invariance, ML training-loop determinism waiver, mandatory compute-budget declaration). Five draft ADRs under `.ai-state/decisions/drafts/` covering verifier extension, tiered backend strategy, `program.md` placement, skill scope, and `TRAINING_RESULTS.md` schema ownership. Implementation deferred to implementation-planner spawn.

## 2026-04-26 — praxion-first-class (Built)

Shipped: `hooks/inject_subagent_context.py` + `hooks/inject_process_framing.py` + `hooks/auto_complete_install.py` + `scripts/render_claude_md.py` + § Praxion Process canonical block in `commands/onboard-project.md`/`commands/new-project.md`. Three draft ADRs under `.ai-state/decisions/drafts/` awaiting finalize.

## 2026-04-24 — project-metrics + tech-debt-integration (Built)

`/project-metrics` slash command + `scripts/project_metrics/` package + `docs/metrics/README.md` schema reference + `docs/metrics/index.html` trend-visualization page; five `/project-metrics` draft ADRs awaiting finalize.

Tech-debt-integration shipped end-to-end: `.ai-state/TECH_DEBT_LEDGER.md` empty artifact + 15-field schema in `rules/swe/agent-intermediate-documents.md` + `scripts/finalize_tech_debt_ledger.py` post-merge dedupe + hook-chain wiring in `scripts/git-post-merge-hook.sh` + verifier Phase 5/5.5 ledger writes + sentinel TD01–TD05 dimension + 5 consumer-contract additions across systems-architect / implementation-planner / implementer / test-engineer / doc-engineer + `## Technical Debt` removed from LEARNINGS template. Three draft ADRs under `.ai-state/decisions/drafts/` finalize to stable `dec-NNN` at merge-to-main.
