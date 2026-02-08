## Software Agent Usage

Conventions for when and how to use the available software agents — autonomous subprocesses that run in separate context windows.

### Available Agents

| Agent | Purpose | Output | When to Use | Background Safe |
|-------|---------|--------|-------------|-----------------|
| `promethean` | Feature-level ideation from project state analysis | `IDEA_PROPOSAL.md` | Generating improvement ideas, exploring gaps, creative exploration of opportunities | No (foreground only -- dialog loop requires user input) |
| `researcher` | Codebase exploration, external docs, comparative analysis | `RESEARCH_FINDINGS.md` | Understanding a technology, evaluating options, gathering context | Yes |
| `systems-architect` | Trade-off analysis, codebase readiness, system design | `SYSTEMS_PLAN.md` | Architectural decisions, structural assessment, technology selection | Yes |
| `implementation-planner` | Step decomposition, execution supervision | `IMPLEMENTATION_PLAN.md`, `WIP.md`, `LEARNINGS.md` | Breaking architecture into increments, resuming multi-session work | Yes |
| `context-engineer` | Context artifact domain expert and implementer — audits, architects, and optimizes context artifacts; collaborates at any pipeline stage when work involves context engineering | Audit report + artifact changes | Auditing quality, resolving conflicts, growing the context ecosystem, providing domain expertise during pipeline work involving context artifacts | Yes |
| `implementer` | Executes individual implementation steps with skill-augmented coding and self-review | Code changes + WIP.md status update | Implementation plan ready with steps to execute | Yes |
| `verifier` | Post-implementation review against acceptance criteria, conventions, and test coverage | `VERIFICATION_REPORT.md` | Validating completed implementation quality before committing | Yes |

### Proactive Agent Usage

Spawn agents without waiting for the user to ask:

- Complex feature request → `researcher` then `systems-architect`
- Architectural decision needed → `systems-architect` (with `researcher` first if unknowns exist)
- Architecture approved and ready for steps → `implementation-planner`
- Context artifacts growing stale or conflicting → `context-engineer`
- Resuming multi-session work → `implementation-planner` to re-assess `WIP.md`
- Research involving context engineering → `researcher` + `context-engineer` in parallel (researcher gathers info, context-engineer provides artifact domain expertise)
- Architecture for context-based systems → `context-engineer` alongside `systems-architect` (context-engineer provides artifact placement, token budget, and progressive disclosure constraints)
- Implementation plan touching context artifacts → `context-engineer` reviews step ordering and crafting spec compliance
- Implementation plan ready with steps to execute → `implementer`
- Implementation complete and plan adherence confirmed → `verifier`

**Depth check:** Before spawning an agent that was recommended by another agent's output, confirm with the user if doing so would create a chain of 3+ agents from the original request.

**Interaction reporting:** When the Task Chronograph MCP server is registered, call `report_interaction` at these key moments:

1. Receiving a user query: `report_interaction(source="user", target="main_agent", summary="...", interaction_type="query")`
2. Delegating to an agent: `report_interaction(source="main_agent", target="{agent_type}", summary="...", interaction_type="delegation")`
3. Receiving an agent's result: `report_interaction(source="{agent_type}", target="main_agent", summary="...", interaction_type="result")`
4. Making a pipeline decision: `report_interaction(source="main_agent", target="main_agent", summary="...", interaction_type="decision")`
5. Responding to the user: `report_interaction(source="main_agent", target="user", summary="...", interaction_type="response")`

### Coordination Pipeline

Agents communicate through shared documents, not direct invocation. Each agent's output is the next agent's input:

```
promethean → IDEA_PROPOSAL.md (optional upstream — when ideation is needed)
    ↓
researcher → RESEARCH_FINDINGS.md
    ↓
systems-architect → SYSTEMS_PLAN.md
    ↓
implementation-planner → IMPLEMENTATION_PLAN.md + WIP.md + LEARNINGS.md
    ↓
implementer → code changes + WIP.md status updates (sequential or parallel)
    ↓
verifier → VERIFICATION_REPORT.md (optional — when quality review is needed)
```

- **Do not skip stages.** If a task needs architecture, it needs research first (unless the codebase context is already sufficient).
- **Re-invoke upstream agents** when a downstream agent discovers the input is incomplete — e.g., the implementation-planner finds the architecture can't be decomposed incrementally.
- **The context-engineer is a domain expert** that can collaborate at any pipeline stage when the work involves context artifacts. It also operates independently for standalone audits.

**Context-Engineer Pipeline Engagement:**

| Pipeline Stage | Context-Engineer Role | Engagement Trigger |
|----------------|----------------------|-------------------|
| Research | Provides domain expertise on context artifacts, evaluates findings through artifact placement lens | Research questions involve context engineering topics |
| Architecture | Supplies artifact type selection, token budget, and progressive disclosure constraints | Architecture affects context artifacts or introduces new conventions |
| Implementation Planning | Reviews step ordering for artifact dependencies, validates crafting spec compliance | Implementation plan includes steps that create, modify, or restructure context artifacts |
| Implementation Execution | Executes artifact steps (create/update/restructure) using crafting skills; planner supervises | Large-scope context work (3+ artifacts, restructuring, ecosystem-wide changes) |
| Verification | N/A — verifier checks code quality and acceptance criteria, not context artifacts | Verifier discovers that planned context artifact updates were skipped (completeness finding routed to context-engineer) |

**Scale-dependent implementation:** For small-scope context work (single artifact — e.g., create one skill, update a rule), the context-engineer implements directly using its crafting skills, no pipeline needed. For large-scope context work (3+ artifacts, restructuring, ecosystem-wide changes), use the full pipeline — the context-engineer executes artifact steps while the implementation-planner supervises.

### Parallel Execution

Launch independent agents concurrently whenever possible:

```
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

### Intra-Stage Parallelism

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

### Multi-Perspective Analysis

For complex or high-risk decisions, use parallel agents with distinct review lenses:

- **Correctness reviewer** — does the design satisfy requirements?
- **Security reviewer** — does the design introduce vulnerabilities?
- **Performance reviewer** — does the design introduce bottlenecks?
- **Maintainability reviewer** — can the team evolve this over time?

Reserve multi-perspective analysis for decisions with significant blast radius. Most tasks need only the standard pipeline.

### Boundary Discipline

Each agent has a defined responsibility — respect the boundaries:

- **Promethean does not research or design.** It ideates — generating and refining ideas through dialog, then writing a proposal. External research and architecture are downstream responsibilities.
- **Researcher does not recommend.** It presents options with trade-offs.
- **Architect does not plan steps.** It designs structure and makes decisions.
- **Implementation planner does not redesign.** It decomposes and supervises.
- **Context engineer does not implement features.** It manages the information architecture. In pipeline mode, it provides domain expertise (artifact placement, token budget, progressive disclosure) — not architectural decisions or implementation steps. It implements context artifacts directly or under planner supervision, but does not implement application features.
- **Implementer does not plan.** It receives a step and implements it. It does not choose what to build, skip steps, reorder the plan, or make go/no-go decisions. It reports blockers with evidence rather than resolving them.
- **Verifier does not fix.** It identifies issues and recommends corrective action through documents. Fixes go back to the implementation-planner (for pipeline work) or the user (for standalone review). It does not check plan adherence (that is Phase 7's job) or assess context artifact quality (that is the context-engineer's job).

When an agent encounters work outside its boundary, it flags the need and recommends invoking the appropriate agent.

### Agent Selection Criteria

When deciding whether to use an agent vs. doing the work directly:

| Situation | Agent | Direct |
|-----------|-------|--------|
| Generating feature-level improvement ideas | Agent (`promethean`) | — |
| Multi-source research with synthesis needed | Agent | — |
| Quick lookup in one file | — | Direct |
| Architecture affecting 3+ components | Agent | — |
| Simple function addition with clear placement | — | Direct |
| Breaking a large feature into incremental steps | Agent | — |
| One-step obvious change | — | Direct |
| Context artifact audit or ecosystem restructuring | Agent (`context-engineer`) | — |
| Single context artifact creation or update | — | Direct (or `context-engineer` for spec compliance) |
| Pipeline work involving 3+ context artifacts | Agent (`context-engineer` + pipeline) | — |
| Multi-file implementation step from a plan | Agent (`implementer`) | — |
| Single obvious code change with clear placement | — | Direct |
| Post-implementation quality review of a complex feature | Agent (`verifier`) | — |
| Quick review of a single-file change | — | Direct (or `code-review` skill) |

**Rule of thumb:** If the task benefits from a separate context window (large scope, multiple phases, structured output), use an agent. If it fits in the current conversation, work directly.

### Background Agents

Run agents in the background when their output is not immediately needed:

- Research tasks that will inform a later decision
- Context audits alongside active development
- Parallel investigation of independent concerns

Never launch a foreground-only agent in the background. Check the Background Safety column in the Available Agents table before using `run_in_background`.

Check background agent output before proceeding with work that depends on their findings. After launching a background agent, periodically check `.ai-work/PROGRESS.md` for status updates.

### Delegation Depth

Track how many agent spawns separate a task from the original user request:

- **Depth 0:** User request handled directly by the main agent — no delegation.
- **Depth 1:** Main agent spawns an agent (e.g., researcher). This is the standard pipeline.
- **Depth 2:** A depth-1 agent's output recommends spawning another agent; the main agent decides whether to proceed. This is the deepest level of automatic chaining.
- **Depth 3+:** Requires explicit user confirmation before proceeding. The main agent presents the recommendation and waits for approval.

**Constraint:** Agents at depth 1 can recommend further agents, but the main agent must not automatically chain to depth 3+ without user confirmation. When in doubt about the current depth, count the number of agent spawns between the original user request and the proposed new agent.

### [CUSTOMIZE] Custom Agents
<!-- Add project-specific agents beyond the standard five:
- Agent name, purpose, output artifact, and when to use
- Where it fits in the coordination pipeline (before/after which stage)
- Whether it can run in parallel with standard agents
-->

### [CUSTOMIZE] Pipeline Overrides
<!-- Adjust coordination pipeline behavior for this project:
- Stages that can be skipped (e.g., skip research when domain is well-known)
- Additional review lenses for multi-perspective analysis
- Project-specific triggers for proactive agent spawning
-->
