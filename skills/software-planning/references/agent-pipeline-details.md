# Agent Pipeline Details

Detailed tables and specifications for the SWE agent coordination pipeline. This reference supplements the always-loaded [coordination protocol rule](../../../rules/swe/swe-agent-coordination-protocol.md) with information agents load on demand.

## Boundary Discipline

| Agent | Does | Does NOT |
|-------|------|----------|
| Promethean | Ideates through dialog, writes proposals | Research, design |
| Researcher | Presents options with trade-offs | Recommend |
| Architect | Designs structure, makes decisions | Plan steps |
| Planner | Decomposes and supervises | Redesign |
| Context Engineer | Manages information architecture, implements context artifacts | Implement features |
| Implementer | Implements steps, makes tests pass, fixes broken pre-existing tests | Plan, skip, reorder steps |
| Test-Engineer | Designs behavioral tests from acceptance criteria, writes test suites concurrently with implementer | Write production code, modify plans |
| Verifier | Identifies issues, recommends actions | Fix issues |
| Doc-engineer | Proactively maintains project documentation at pipeline checkpoints | Manage context artifacts |
| Sentinel | Diagnoses and reports across ecosystem | Fix artifacts |
| Skill-Genesis | Triages learnings into artifact proposals, delegates creation | Ideate features, audit ecosystem, create artifacts |
| CI/CD Engineer | Designs and writes CI/CD pipelines, optimizes and debugs workflows | Modify application code, manage infrastructure |

When an agent encounters work outside its boundary, it flags the need and recommends invoking the appropriate agent.

## Agent Selection Criteria

| Situation | Use |
|-----------|-----|
| Multi-source research, architecture 3+ components, large feature decomposition | Agent |
| Ecosystem audit or 3+ context artifacts | `context-engineer` or `sentinel` |
| Complex test design, test suite refactoring, testing infrastructure setup | `test-engineer` |
| Post-implementation quality review | `verifier` |
| Documentation scope assessment, post-implementation doc updates, cross-reference fixes | `doc-engineer` |
| Feature-level ideation from project state | `promethean` |
| Post-pipeline learning harvest or 3+ accumulated LEARNINGS.md entries | `skill-genesis` |

## Parallel Execution

Launch independent agents concurrently whenever possible.

| Parallelize | Do Not Parallelize |
|-------------|--------------------|
| Multiple independent research questions | One agent's output feeds the next (pipeline dependency) |
| Separate codebase areas needing analysis | Two agents analyzing and modifying the same files |
| Context audit alongside development planning | |
| Doc-engineer alongside implementer or verifier | |
| Implementer + test-engineer on paired steps (disjoint: production vs test files) | Implementer + test-engineer modifying the same files |
| N same-type agents on disjoint work units (see Intra-Stage Parallelism) | Same-type agents whose file sets overlap |
| Context-engineer alongside researcher or systems-architect | |

## Intra-Stage Parallelism

Multiple instances of the same agent type can run concurrently on disjoint work units within a single pipeline stage. Distinct from cross-agent parallelism above. Limit to 2-3 concurrent agents.

**Direct-supervised** (any Bg Safe agent):

1. Main agent identifies N independent work units with disjoint file sets
2. Spawns N instances with `isolation: "worktree"` when agents modify files, each scoped to its target via the task prompt
3. Each instance reports independently
4. Main agent reviews all outputs for coherence

**Planner-supervised** (implementer/test-engineer under implementation-planner):

1. Planner prepares `WIP.md` in parallel mode with per-step assignees and file lists
2. Main agent spawns N implementer or test-engineer agents with `isolation: "worktree"`, each assigned one step
3. Each agent updates only its own step status in `WIP.md`
4. After all report back, planner runs coherence review (re-reads modified files, verifies integration, merges learnings)

**Conflict avoidance:** Before spawning parallel instances, verify file disjointness across all work units. If an agent needs a file outside its declared set, it stops and reports `[CONFLICT]`.

## Multi-Perspective Analysis

For high-risk decisions, use parallel agents with distinct lenses: **correctness** (requirements satisfied?), **security** (vulnerabilities introduced?), **performance** (bottlenecks?), **maintainability** (evolvable?). Reserve for decisions with significant blast radius; most tasks need only the standard pipeline.

## Context-Engineer Pipeline Engagement

| Stage | Role | Trigger |
|-------|------|---------|
| Research | Domain expertise on context artifacts; evaluates findings through artifact placement lens | Research involves context engineering topics |
| Architecture | Artifact type selection, token budget, progressive disclosure constraints | Architecture affects context artifacts or introduces new conventions |
| Planning | Reviews step ordering for artifact dependencies, validates crafting spec compliance | Plan creates, modifies, or restructures context artifacts |
| Execution | Executes artifact steps using crafting skills; planner supervises | Large-scope context work (3+ artifacts, restructuring) |
| Verification | N/A (verifier checks code, not context artifacts) | Verifier finds planned context updates were skipped --> routes to context-engineer |

**Scale:** Single artifact --> context-engineer directly. 3+ artifacts or restructuring --> full pipeline under planner supervision.

## Doc-Engineer Pipeline Engagement

| Stage | Role | Trigger |
|-------|------|---------|
| Planning | Assess existing documentation in the affected area; flag docs that will need updates | Plan touches area with README, catalog, or architecture docs |
| Implementation | Update affected READMEs, catalogs, changelogs after code changes | Implementation adds, removes, or renames files; new public APIs or interfaces |
| Refactoring | Sync documentation with structural changes | Refactoring moves, renames, or reorganizes modules or directories |
| Verification | N/A (verifier checks code) | Verifier finds documentation updates were planned but not executed --> routes to doc-engineer |

**Timing:** Runs in background parallel with other agents when its work is independent. Post-implementation documentation updates can run alongside the verifier.

## Interaction Reporting

When the Task Chronograph MCP server is registered, call `report_interaction(source, target, summary, interaction_type)` at these moments:

| Moment | source | target | interaction_type |
|--------|--------|--------|-----------------|
| Receiving user query | `"user"` | `"main_agent"` | `"query"` |
| Delegating to agent | `"main_agent"` | `"{agent_type}"` | `"delegation"` |
| Receiving agent result | `"{agent_type}"` | `"main_agent"` | `"result"` |
| Making pipeline decision | `"main_agent"` | `"main_agent"` | `"decision"` |
| Responding to user | `"main_agent"` | `"user"` | `"response"` |
