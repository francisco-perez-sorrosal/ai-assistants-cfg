## Software Agent Usage

Conventions for when and how to use the available software agents — autonomous subprocesses that run in separate context windows.

### Available Agents

| Agent | Purpose | Output | When to Use | Background Safe |
|-------|---------|--------|-------------|-----------------|
| `promethean` | Feature-level ideation from project state, optionally consuming sentinel reports | `IDEA_PROPOSAL.md` (`.ai-work/`), `IDEA_LEDGER_*.md` (`.ai-state/`) | Generating improvement ideas, exploring gaps and opportunities | No (foreground only) |
| `researcher` | Codebase exploration, external docs, comparative analysis | `RESEARCH_FINDINGS.md` | Understanding a technology, evaluating options, gathering context | Yes |
| `systems-architect` | Trade-off analysis, codebase readiness, system design | `SYSTEMS_PLAN.md` | Architectural decisions, structural assessment, technology selection | Yes |
| `implementation-planner` | Step decomposition, execution supervision | `IMPLEMENTATION_PLAN.md`, `WIP.md`, `LEARNINGS.md` | Breaking architecture into increments, resuming multi-session work | Yes |
| `context-engineer` | Context artifact domain expert — audits, architects, optimizes; collaborates at any pipeline stage | Audit report + artifact changes | Auditing quality, resolving conflicts, growing ecosystem, domain expertise in pipeline work | Yes |
| `implementer` | Executes individual implementation steps with skill-augmented coding and self-review | Code changes + WIP.md status update | Implementation plan ready with steps to execute | Yes |
| `verifier` | Post-implementation review against acceptance criteria, conventions, and test coverage | `VERIFICATION_REPORT.md` | Validating completed implementation quality before committing | Yes |
| `doc-engineer` | Project-facing documentation quality management (README.md, catalogs, architecture docs, changelogs) | Documentation quality report or direct file fixes | After implementation changes, when creating or auditing documentation | Yes |
| `sentinel` | Read-only ecosystem quality auditor across eight dimensions. Independent — not a pipeline stage | `SENTINEL_REPORT_*.md` + `SENTINEL_LOG.md` (`.ai-state/`) | Ecosystem health checks, pre-pipeline baselines, post-change regression detection | Yes |

### Proactive Agent Usage

Spawn agents without waiting for the user to ask:

- Complex feature request → `researcher` then `systems-architect`
- Architectural decision needed → `systems-architect` (with `researcher` first if unknowns exist)
- Architecture approved and ready for steps → `implementation-planner`
- Context artifacts growing stale or conflicting → `context-engineer`
- Resuming multi-session work → `implementation-planner` to re-assess `WIP.md`
- Context engineering research or architecture → `context-engineer` in parallel with `researcher` or `systems-architect`
- Implementation plan touching context artifacts → `context-engineer` reviews step ordering and crafting spec compliance
- Implementation plan ready with steps to execute → `implementer`
- Implementation complete and plan adherence confirmed → `verifier`
- Ecosystem health check needed → `sentinel`
- Before major pipeline runs (baseline quality) → `sentinel`
- After large artifact changes (regression detection) → `sentinel`
- Sentinel report may be stale → check `.ai-state/SENTINEL_LOG.md` vs `git log -1 --format=%ci`; run `sentinel` if commits exist after last report
- After implementation changes that add/remove/rename files → `doc-engineer`
- After context-engineer creates new artifacts that need catalog entries → `doc-engineer`

**Depth check:** Before spawning an agent that was recommended by another agent's output, confirm with the user if doing so would create a chain of 3+ agents from the original request.

For interaction reporting protocol (Task Chronograph), see `rules/swe/references/agent-coordination-protocols.md`.

### Coordination Pipeline

Agents communicate through shared documents, not direct invocation. Each agent's output is the next agent's input:

```
promethean → IDEA_PROPOSAL.md + IDEA_LEDGER_*.md
    ↓
researcher → RESEARCH_FINDINGS.md
    ↓                              ┌─────────────────┐
systems-architect → SYSTEMS_PLAN.md    │ context-engineer │
    ↓                              │  (domain expert  │
implementation-planner → IMPL...   │   at any stage)  │
    ↓                              └─────────────────┘
implementer → code changes         ┌─────────────────┐
    ↓                              │    sentinel      │
verifier → VERIFICATION_REPORT.md  │  (independent    │
                                   │   audit — any    │
                                   │   agent/user can │
                                   │   read reports)  │
                                   └─────────────────┘
```

- **Do not skip stages.** If a task needs architecture, it needs research first (unless the codebase context is already sufficient).
- **Re-invoke upstream agents** when a downstream agent discovers the input is incomplete — e.g., the implementation-planner finds the architecture can't be decomposed incrementally.
- **The context-engineer is a domain expert** that can collaborate at any pipeline stage when the work involves context artifacts. It also operates independently for standalone audits.
- **The sentinel is an independent audit tool** that runs on demand. Its reports (`SENTINEL_REPORT_*.md`) are public — any agent or user can consume them. The promethean may read them as input for ideation, but that is the promethean's choice, not a pipeline handoff from the sentinel.

For context-engineer engagement details at each pipeline stage, see `rules/swe/references/agent-coordination-protocols.md`. For small-scope context work (single artifact), the context-engineer implements directly; for large-scope (3+ artifacts), use the full pipeline.

For parallel execution protocols and examples, see `rules/swe/references/agent-coordination-protocols.md`.

### Boundary Discipline

| Agent | Does | Does NOT |
|-------|------|----------|
| Promethean | Ideates through dialog, writes proposals | Research, design |
| Researcher | Presents options with trade-offs | Recommend |
| Architect | Designs structure, makes decisions | Plan steps |
| Planner | Decomposes and supervises | Redesign |
| Context Engineer | Manages information architecture, implements context artifacts | Implement features |
| Implementer | Receives and implements steps | Plan, skip, reorder steps |
| Verifier | Identifies issues, recommends actions | Fix issues |
| Doc-engineer | Maintains project documentation | Manage context artifacts |
| Sentinel | Diagnoses and reports across ecosystem | Fix artifacts |

When an agent encounters work outside its boundary, it flags the need and recommends invoking the appropriate agent.

### Agent Selection Criteria

**Rule of thumb:** Use an agent when the task benefits from a separate context window (large scope, multiple phases, structured output). Work directly when it fits in the current conversation.

| Situation | Use |
|-----------|-----|
| Multi-source research, architecture affecting 3+ components, breaking large features into steps | Agent |
| Quick lookup, single obvious change, one-step edit | Direct |
| Ecosystem audit or 3+ context artifacts | Agent (`context-engineer` or `sentinel`) |
| Post-implementation quality review | Agent (`verifier`) |
| Documentation audit or cross-reference fixes | Agent (`doc-engineer`) |
| Feature-level ideation from project state | Agent (`promethean`) |

### Background Agents

Run agents in the background when their output is not immediately needed:

- Research tasks that will inform a later decision
- Context audits alongside active development
- Parallel investigation of independent concerns

Never launch a foreground-only agent in the background. Check the Background Safety column in the Available Agents table before using `run_in_background`.

Check background agent output before proceeding with dependent work. Monitor `.ai-work/PROGRESS.md` for status.

### Delegation Depth

- **Depth 0-1:** Standard — main agent handles directly or spawns one agent.
- **Depth 2:** A depth-1 agent's output recommends another agent; main agent decides whether to proceed.
- **Depth 3+:** Requires explicit user confirmation before proceeding.

Agents at depth 1 can recommend further agents, but never auto-chain to depth 3+ without user confirmation.
