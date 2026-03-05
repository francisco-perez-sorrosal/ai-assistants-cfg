## SWE Agent Coordination Protocol

Conventions for when and how to use the available software agents -- autonomous subprocesses that run in separate context windows.

### Available Agents

| Agent | Purpose | Output | Bg Safe |
|-------|---------|--------|---------|
| `promethean` | Feature-level ideation from project state | `IDEA_PROPOSAL.md`, `IDEA_LEDGER_*.md` | No |
| `researcher` | Codebase exploration, external docs, comparative analysis | `RESEARCH_FINDINGS.md` | Yes |
| `systems-architect` | Trade-off analysis, system design | `SYSTEMS_PLAN.md` | Yes |
| `implementation-planner` | Step decomposition, execution supervision | `IMPLEMENTATION_PLAN.md`, `WIP.md`, `LEARNINGS.md` | Yes |
| `context-engineer` | Context artifact domain expert; any pipeline stage | Audit report + artifact changes | Yes |
| `implementer` | Executes implementation steps with self-review | Code changes + `WIP.md` update | Yes |
| `test-engineer` | Dedicated testing: complex test design, test suite refactoring, testing infrastructure | Test code + `WIP.md` update | Yes |
| `verifier` | Post-implementation review against acceptance criteria | `VERIFICATION_REPORT.md` | Yes |
| `doc-engineer` | Documentation quality (READMEs, catalogs, changelogs) | Doc report or file fixes | Yes |
| `sentinel` | Read-only ecosystem auditor (independent, not a pipeline stage) | `SENTINEL_REPORT_*.md`, `SENTINEL_LOG.md` | Yes |
| `skill-genesis` | Learning triage, artifact proposal from experience | `SKILL_GENESIS_REPORT.md` | No |
| `cicd-engineer` | CI/CD pipeline design, GitHub Actions, deployment automation | Workflow files + pipeline config | Yes |

### Proactive Agent Usage

Spawn agents without waiting for the user to ask:

- Complex feature --> `researcher` then `systems-architect` (skip researcher if codebase context suffices)
- Architecture approved --> `implementation-planner`; resuming work --> same agent to re-assess `WIP.md`
- Plan ready --> `implementer` + `test-engineer` concurrently (paired steps on disjoint file sets); both complete --> run tests --> fix cycle if needed --> `verifier`
- Context artifacts stale/conflicting or plan touches them --> `context-engineer` (parallel with `researcher`/`systems-architect`)
- Ecosystem health or regression check --> `sentinel`; stale check: `.ai-state/SENTINEL_LOG.md` vs `git log -1 --format=%ci`
- Documentation impact likely --> `doc-engineer` (in background): feature planned in area with existing docs, implementation or refactoring complete, files added/removed/renamed, new public API or interface
- Pipeline complete + LEARNINGS.md has content --> `skill-genesis`

**Depth check:** Before spawning an agent recommended by another agent's output, confirm with the user if doing so would create a chain of 3+ agents from the original request.

**Multiplicity check:** Before spawning any Bg Safe agent, check whether the work decomposes into N independent targets with disjoint file sets. If so, spawn N instances (up to 2-3 concurrent) rather than one sequential agent.

### Coordination Pipeline

Agents communicate through shared documents, not direct invocation.

```text
promethean --> researcher --> systems-architect --> implementation-planner --+--> implementer    --+--> verifier
                                                                            |                     |
                                                                            +--> test-engineer  --+
                                                                     context-engineer (any stage)
                                                                     doc-engineer (pipeline checkpoints)
                                                                     sentinel (independent audit)
```

**Pipeline rules:**

- **Do not skip stages.** Research before architecture (unless codebase context suffices). Re-invoke upstream agents when downstream input is incomplete.
- **BDD/TDD execution.** The planner produces paired implementation and test steps. Test-engineers design behavioral tests from the systems plan's acceptance criteria. Implementers and test-engineers execute concurrently on disjoint file sets. After both complete, tests are run against the implementation. Failing tests trigger a fix cycle until all tests pass — including pre-existing tests broken by the change (boy scout rule).
- **Context-engineer** collaborates at any pipeline stage for context artifact work. Also operates independently for standalone audits.
- **Sentinel** is independent. Reports (`SENTINEL_REPORT_*.md`) are public -- any agent or user can consume them.
- Small-scope context work (single artifact) --> context-engineer directly; large-scope (3+) --> full pipeline.
- **Doc-engineer** is a proactive pipeline participant. Invoke at natural checkpoints: after planning (assess documentation scope), after implementation (update affected docs), after refactoring (sync docs with structural changes).

### Agent Selection Criteria

Use an agent when the task benefits from a separate context window (large scope, multiple phases, structured output). Work directly for quick lookups, single changes, one-step edits.

### Delegation Depth

- **Depth 0-1:** Standard. **Depth 2:** Main agent decides. **Depth 3+:** Requires explicit user confirmation.
- Agents at depth 1 can recommend further agents but never auto-chain to depth 3+.

### Background Agents

Run agents in the background when their output is not immediately needed. Check the Bg Safe column before using `run_in_background`. Monitor `.ai-work/PROGRESS.md` for status; check output before proceeding with dependent work.

### Parallel Execution & Boundary Discipline

Launch independent agents concurrently whenever possible. Each agent has strict boundaries — when an agent encounters work outside its boundary, it flags the need and recommends invoking the appropriate agent.

For detailed tables on boundary discipline, parallel execution rules, intra-stage parallelism, multi-perspective analysis, context-engineer and doc-engineer pipeline engagement, and interaction reporting, load the `software-planning` skill's [agent-pipeline-details.md](../../skills/software-planning/references/agent-pipeline-details.md) reference.
