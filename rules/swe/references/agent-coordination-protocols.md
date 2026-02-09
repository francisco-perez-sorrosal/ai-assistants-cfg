# Agent Coordination Protocols

Advanced coordination protocols for multi-agent execution. These protocols are loaded on demand when parallel execution, intra-stage parallelism, multi-perspective analysis, or context-engineer pipeline engagement is needed.

## Pipeline Diagram

```text
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

### Pipeline Rules

- **Do not skip stages.** If a task needs architecture, it needs research first (unless the codebase context is already sufficient).
- **Re-invoke upstream agents** when a downstream agent discovers the input is incomplete — e.g., the implementation-planner finds the architecture can't be decomposed incrementally.
- **The context-engineer is a domain expert** that can collaborate at any pipeline stage when the work involves context artifacts. It also operates independently for standalone audits.
- **The sentinel is an independent audit tool** that runs on demand. Its reports (`SENTINEL_REPORT_*.md`) are public — any agent or user can consume them. The promethean may read them as input for ideation, but that is the promethean's choice, not a pipeline handoff from the sentinel.

## Parallel Execution

Launch independent agents concurrently whenever possible:

```text
# GOOD — parallel when independent
Launch in parallel:
  1. researcher: investigate authentication library options
  2. researcher: audit current database schema patterns

# GOOD — context-engineer alongside pipeline agent
Launch in parallel:
  1. researcher: investigate skill activation patterns
  2. context-engineer: assess current skill ecosystem for conflicts and gaps

# GOOD — domain expertise alongside architecture
Launch in parallel:
  1. systems-architect: design new rule organization
  2. context-engineer: provide artifact placement and token budget constraints

# BAD — sequential when unnecessary
First research auth, then research database (no dependency between them)
```

**Parallelize when:**

- Multiple independent research questions exist
- Different parts of the codebase need separate analysis
- A context audit can run alongside development planning

**Do not parallelize when:**

- One agent's output is the next agent's input (the pipeline)
- Two agents would analyze and modify the same files

## Intra-Stage Parallelism

Multiple instances of the same agent type can run concurrently on disjoint work units within a single pipeline stage. This is distinct from cross-agent parallelism (different agent types running independently).

**When to use:**

- Implementation steps in the same `[parallel-group]` with disjoint file sets
- No shared mutable state between the concurrent steps

**Batch size:** Limit to 2-3 concurrent agents. More increases coordination overhead without proportional throughput gain.

**Coordination protocol:**

1. The implementation-planner prepares WIP.md in parallel mode with per-step assignees and file lists
2. The user spawns N implementer agents concurrently, each assigned one step
3. Each implementer updates only its own step's status in WIP.md
4. After all implementers report back, the planner runs a coherence review (re-reads all modified files, verifies integration, merges step-specific learnings)

**Conflict avoidance:**

- The planner verifies file disjointness before marking steps as parallel
- If an implementer discovers it needs a file outside its declared set, it stops and reports `[CONFLICT]`

## Multi-Perspective Analysis

For complex or high-risk decisions, use parallel agents with distinct review lenses:

- **Correctness reviewer** — does the design satisfy requirements?
- **Security reviewer** — does the design introduce vulnerabilities?
- **Performance reviewer** — does the design introduce bottlenecks?
- **Maintainability reviewer** — can the team evolve this over time?

Reserve multi-perspective analysis for decisions with significant blast radius. Most tasks need only the standard pipeline.

## Context-Engineer Pipeline Engagement

| Pipeline Stage | Context-Engineer Role | Engagement Trigger |
|----------------|----------------------|-------------------|
| Research | Provides domain expertise on context artifacts, evaluates findings through artifact placement lens | Research questions involve context engineering topics |
| Architecture | Supplies artifact type selection, token budget, and progressive disclosure constraints | Architecture affects context artifacts or introduces new conventions |
| Implementation Planning | Reviews step ordering for artifact dependencies, validates crafting spec compliance | Implementation plan includes steps that create, modify, or restructure context artifacts |
| Implementation Execution | Executes artifact steps (create/update/restructure) using crafting skills; planner supervises | Large-scope context work (3+ artifacts, restructuring, ecosystem-wide changes) |
| Verification | N/A — verifier checks code quality and acceptance criteria, not context artifacts | Verifier discovers that planned context artifact updates were skipped (completeness finding routed to context-engineer) |

**Scale-dependent implementation:** For small-scope context work (single artifact — e.g., create one skill, update a rule), the context-engineer implements directly using its crafting skills, no pipeline needed. For large-scope context work (3+ artifacts, restructuring, ecosystem-wide changes), use the full pipeline — the context-engineer executes artifact steps while the implementation-planner supervises.

## Interaction Reporting

When the Task Chronograph MCP server is registered, call `report_interaction` at these key moments:

1. Receiving a user query: `report_interaction(source="user", target="main_agent", summary="...", interaction_type="query")`
2. Delegating to an agent: `report_interaction(source="main_agent", target="{agent_type}", summary="...", interaction_type="delegation")`
3. Receiving an agent's result: `report_interaction(source="{agent_type}", target="main_agent", summary="...", interaction_type="result")`
4. Making a pipeline decision: `report_interaction(source="main_agent", target="main_agent", summary="...", interaction_type="decision")`
5. Responding to the user: `report_interaction(source="main_agent", target="user", summary="...", interaction_type="response")`
