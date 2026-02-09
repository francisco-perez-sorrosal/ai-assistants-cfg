## Software Agent Usage

Conventions for when and how to use the available software agents — autonomous subprocesses that run in separate context windows.

### Available Agents

| Agent | Purpose | Output | When to Use | Bg Safe |
|-------|---------|--------|-------------|---------|
| `promethean` | Feature-level ideation from project state | `IDEA_PROPOSAL.md`, `IDEA_LEDGER_*.md` | Generating ideas, exploring gaps | No |
| `researcher` | Codebase exploration, external docs, comparative analysis | `RESEARCH_FINDINGS.md` | Evaluating options, gathering context | Yes |
| `systems-architect` | Trade-off analysis, system design | `SYSTEMS_PLAN.md` | Architectural decisions, technology selection | Yes |
| `implementation-planner` | Step decomposition, execution supervision | `IMPLEMENTATION_PLAN.md`, `WIP.md`, `LEARNINGS.md` | Breaking architecture into increments, resuming work | Yes |
| `context-engineer` | Context artifact domain expert; collaborates at any pipeline stage | Audit report + artifact changes | Auditing, resolving conflicts, ecosystem growth | Yes |
| `implementer` | Executes implementation steps with self-review | Code changes + `WIP.md` update | Implementation plan ready with steps | Yes |
| `verifier` | Post-implementation review against acceptance criteria and conventions | `VERIFICATION_REPORT.md` | Validating quality before committing | Yes |
| `doc-engineer` | Documentation quality management (READMEs, catalogs, changelogs) | Doc report or file fixes | After changes that affect documentation | Yes |
| `sentinel` | Read-only ecosystem quality auditor (independent, not a pipeline stage) | `SENTINEL_REPORT_*.md`, `SENTINEL_LOG.md` | Health checks, baselines, regression detection | Yes |

### Proactive Agent Usage

Spawn agents without waiting for the user to ask:

- Complex feature → `researcher` then `systems-architect` (skip researcher if codebase context suffices)
- Architecture approved → `implementation-planner`; resuming multi-session work → same agent to re-assess `WIP.md`
- Plan ready with steps → `implementer`; implementation complete → `verifier`
- Context artifacts stale/conflicting or plan touches context artifacts → `context-engineer` (can run in parallel with `researcher` or `systems-architect`)
- Ecosystem health, pre-pipeline baseline, or post-change regression → `sentinel`; stale check: compare `.ai-state/SENTINEL_LOG.md` vs `git log -1 --format=%ci`
- After changes that add/remove/rename files or new artifacts need catalog entries → `doc-engineer`

**Depth check:** Before spawning an agent recommended by another agent's output, confirm with the user if doing so would create a chain of 3+ agents from the original request.

For interaction reporting protocol (Task Chronograph), see `rules/swe/references/agent-coordination-protocols.md`.

### Coordination Pipeline

Agents communicate through shared documents, not direct invocation: `promethean → researcher → systems-architect → implementation-planner → implementer → verifier`. The context-engineer collaborates at any stage; the sentinel runs independently.

- **Do not skip stages.** Re-invoke upstream agents when downstream input is incomplete.
- Small-scope context work (single artifact) → context-engineer directly; large-scope (3+) → full pipeline.

For the pipeline diagram, parallel execution protocols, and context-engineer engagement details, see `rules/swe/references/agent-coordination-protocols.md`.

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

Run agents in the background when their output is not immediately needed (research, audits, parallel investigation). Check the Bg Safe column before using `run_in_background`. Monitor `.ai-work/PROGRESS.md` for status; check output before proceeding with dependent work.

### Delegation Depth

- **Depth 0-1:** Standard. **Depth 2:** Main agent decides. **Depth 3+:** Requires explicit user confirmation.
- Agents at depth 1 can recommend further agents but never auto-chain to depth 3+.
