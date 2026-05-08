# Architecture Changelog

Append-only history of `ARCHITECTURE.md` verification milestones. Each entry summarizes a feature pipeline that updated the architect-facing design-target document. Owned by systems-architect; appended by the implementer/verifier of each feature.

The current "Last verified" pointer in `.ai-state/ARCHITECTURE.md` § 1 is a one-liner referencing the most recent entry below; deep history lives here so the architecture doc stays scannable.

---

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
