# Roadmap — Handoff from verifier-rework-loop session

**Status**: Handoff snapshot, not a living roadmap. Per `dec-092`, Praxion does not maintain a living `ROADMAP.md`; the cartographer regenerates one on demand via `/roadmap`. This file captures three follow-up topics surfaced during the verifier-rework-loop pipeline session so they can be addressed in separate, focused sessions. Run `/roadmap` if you want a full project-audited roadmap instead — it will replace this file.

**Generated**: 2026-05-14 — post-merge of `worktree-verifier-rework-loop` to `main` (commit `c607343`).

---

## Topic 1 — Multi-worktree rework orchestration from a single Claude session

**Surfaced by**: The rework-loop dogfood at the end of the pipeline. After the verifier emitted a 4-row `REWORK_MANIFEST.md` and the main agent spawned 3 rework worktrees, the user had to manually open a fresh Claude Code session in each worktree and run `/resume-rework` — three separate terminals, three separate sessions, three manual context-switches. This pauses the development flow at exactly the moment when the rework loop should be at its most efficient.

**The friction in one sentence**: the rework loop's design is fully functional but the user-facing dispatch UX assumes the user enjoys juggling terminal windows.

**Approaches worth exploring** (any combination):

1. **Helper script + macOS terminal automation** — A `scripts/praxion-dispatch-reworks` (or `commands/dispatch-reworks.md`) that reads `REWORK_MANIFEST.md`, opens N new terminal windows via `osascript` (or `wezterm cli`, `iterm2 python api`), each pre-cd'd into its rework worktree and ready to run `/resume-rework`. The actual `/resume-rework` invocation can either auto-fire (security implications) or wait for the user to hit enter (safer).
2. **tmux-based dispatch** — A `praxion-rework-tmux` helper that creates N panes/windows in a tmux session, each cd'd into its rework worktree with `claude` ready. Cross-platform, persistent across reconnects. Cost: requires tmux.
3. **Sequential dispatch in the same session** — A slash command that processes reworks *sequentially* using `ExitWorktree` + `EnterWorktree` between each. Single session, no extra terminals. Cost: loses parallelism — reworks queue rather than run concurrently.
4. **Direct integration with Claude Code's session-management surface** — If Claude Code exposes a programmatic "open a new session in directory X with prompt Y" API, build on that. If not, file a feature request.

**Related**: `td-035` (the worktree_guard collision) lives in the same architectural surface — both are about the main agent's relationship to rework worktrees.

**Scope estimate**: Standard tier (4-8 files, 2-4 behaviors, architectural decisions). The macOS-only AppleScript approach is the lowest-friction MVP; tmux is the most portable; sequential is the safest fallback.

---

## Topic 2 — Documentation + architecture + diagram review for the new pipeline loops

**Surfaced by**: Two substantive feedback loops landed recently in Praxion's agent pipeline:

- **Researcher → Architect (CIS, forward-feeding)** — The Continuous Improvement Signals feature: researcher's Hat 2 surfaces strict-improvement candidates for incumbent libraries/frameworks; architect dispositions each via switch-now / defer-with-rationale / dismiss-with-rationale.
- **Verifier → Architect / Planner (Rework Loop, backward-feeding)** — The verifier-rework-loop feature this session built: verifier's Phase 12.5 emits `REWORK_MANIFEST.md`; main agent spawns rework worktrees with `VERIFIER_FINDINGS.md`; user runs `/resume-rework` to dispatch the architect.

Both share a disposition vocabulary (single source: `skills/software-planning/references/disposition-vocabulary.md`). Both modify the pipeline's previously-linear flow (researcher → architect → planner → implementer → verifier) into a graph with backward edges.

The existing architecture documents may not reflect this clearly:

- `.ai-state/DESIGN.md` — architect-facing design-target — has rework-loop components but may not have a clean diagrammatic representation of the two loops
- `docs/architecture.md` — code-verified developer guide — has the rework-loop section §10 but doesn't characterize the bidirectional shape of the pipeline
- LikeC4 sources under `docs/diagrams/architecture/src/` — the model may still show a linear pipeline
- `agents/README.md` catalog — may not surface "this agent participates in feedback loops back to X"

**Suggested approach**:
1. Run `/sentinel` first — surfaces staleness + cross-reference issues across the ecosystem
2. Run `/roadmap diff` (or full cartographer) — produces a fresh audit including the doc/diagram health dimension
3. Delegate the diagram work to `systems-architect` (LikeC4 model update + rendered diagram refresh per `rules/writing/diagram-conventions.md`)
4. Delegate the narrative-doc work to `doc-engineer` (DESIGN.md + docs/architecture.md + agents/README.md)

**Related ADRs**: `dec-173` through `dec-182` (rework-loop) + the earlier CIS-related drafts on main (need to grep). All ten are now finalized; cross-references rewritten.

**Scope estimate**: Standard tier with `doc-engineer` + `systems-architect` as primary executors. Could be Full if the LikeC4 model needs substantial restructuring.

---

## Topic 3 — Skill-genesis UX: post-merge friction + SendMessage limitation

**Surfaced by**: At the end of the verifier-rework-loop pipeline, skill-genesis was invoked to harvest patterns from `LEARNINGS.md` before the final merge. Two problems emerged:

1. **The interactive AskUserQuestion-per-proposal pattern paused the agent mid-run.** Skill-genesis presented Proposal 1 of 4 and waited for the user's disposition. The user dispositioned it, but the agent couldn't be resumed: `SendMessage` is not available in the current Claude Code tool surface, and subagents cannot spawn other agents (confirmed convention per `agents/CLAUDE.md`). The orchestrator (main agent) had to materialize Proposal 1 manually and explicitly skip Proposals 2-4.
2. **Skill-genesis runs at end-of-pipeline, right at the moment when the user is least interested in another decision cycle.** A long pipeline just landed, the merge succeeded, ADRs were finalized — and *then* the system asks "by the way, want to harvest 4 patterns into new skills?" The cognitive load lands on top of an already-saturated session.

**Concrete improvements worth exploring**:

- **Mode change: autonomous skill-genesis with deferred review** — Skill-genesis runs without user interaction, writes a `SKILL_GENESIS_REPORT.md` with all proposals classified by maturity / scope / priority, and the user disposition later via a `/skill-genesis-review` command (a separate, opt-in moment). The merge moment is heavy; skill-genesis becomes pull-driven rather than push-driven.
- **Batch disposition: single AskUserQuestion with N options** — If skill-genesis stays interactive, present all N proposals in *one* `AskUserQuestion` (multi-select) rather than N separate ones. User dispositions in one shot. Reduces session interruptions from N to 1.
- **Decouple from merge: skill-genesis as a periodic Praxion command** — Rather than firing at the end of every pipeline, skill-genesis becomes `/skill-genesis` invoked on demand (similar to `/sentinel`). The pipeline writes `LEARNINGS.md`; skill-genesis is a separate maintenance pass.
- **SendMessage feature request to Claude Code** — File an issue. The pattern of "orchestrator pauses subagent, user dispositions, orchestrator resumes subagent" is general; many features beyond skill-genesis would benefit.

**Confirmed limitation**: Subagents cannot spawn other agents. This is by design (preserves coordination centralization, bounds recursion). The `SendMessage` limitation is a different gap — the orchestrator's inability to *resume* a paused subagent — and exists in the current Claude Code tool surface, not Praxion's design.

**Scope estimate**: Small-Medium. The "autonomous mode + SKILL_GENESIS_REPORT.md" change is primarily prompt engineering on `agents/skill-genesis.md`. The batch-disposition change is small. Decoupling from merge is a coordination-protocol rule edit. The SendMessage feature request is external.

**Related**: `agents/skill-genesis.md`, `rules/swe/swe-agent-coordination-protocol.md` (when skill-genesis fires), `skills/software-planning/references/coordination-details.md`.

---

## What this roadmap intentionally does NOT include

- Performance metrics, GTM analysis, lens-derived audits — that's `/roadmap`'s job
- Implementation steps for each topic — those belong in each topic's own SYSTEMS_PLAN.md when its session starts
- Prioritization order — the topics are independent; do them in whatever order makes sense
- Dates / deadlines — Praxion's pace is intrinsic, not externally clocked

---

## How to use this file

Pick one topic, open a new Claude Code session in the main checkout, and tell Claude "let's address Topic N from ROADMAP.md." The session can be Direct, Lightweight, Standard, or Full tier per the scope estimate. After all three topics are addressed (or you've decided to defer some), this file can be deleted — or replaced by a fresh `/roadmap` run for a comprehensive audit.
