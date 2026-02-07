## Software Agent Usage

Conventions for when and how to use the available software agents — autonomous subprocesses that run in separate context windows.

### Available Agents

| Agent | Purpose | Output | When to Use |
|-------|---------|--------|-------------|
| `researcher` | Codebase exploration, external docs, comparative analysis | `RESEARCH_FINDINGS.md` | Understanding a technology, evaluating options, gathering context |
| `systems-architect` | Trade-off analysis, codebase readiness, system design | `SYSTEMS_PLAN.md` | Architectural decisions, structural assessment, technology selection |
| `implementation-planner` | Step decomposition, execution supervision | `IMPLEMENTATION_PLAN.md`, `WIP.md`, `LEARNINGS.md` | Breaking architecture into increments, resuming multi-session work |
| `context-engineer` | Context artifact auditing, optimization, ecosystem management | Audit report + artifact changes | Auditing quality, resolving conflicts, growing the context ecosystem |

### Proactive Agent Usage

Spawn agents without waiting for the user to ask:

- Complex feature request → `researcher` then `systems-architect`
- Architectural decision needed → `systems-architect` (with `researcher` first if unknowns exist)
- Architecture approved and ready for steps → `implementation-planner`
- Context artifacts growing stale or conflicting → `context-engineer`
- Resuming multi-session work → `implementation-planner` to re-assess `WIP.md`

### Coordination Pipeline

Agents communicate through shared documents, not direct invocation. Each agent's output is the next agent's input:

```
researcher → RESEARCH_FINDINGS.md
    ↓
systems-architect → SYSTEMS_PLAN.md
    ↓
implementation-planner → IMPLEMENTATION_PLAN.md + WIP.md + LEARNINGS.md
```

- **Do not skip stages.** If a task needs architecture, it needs research first (unless the codebase context is already sufficient).
- **Re-invoke upstream agents** when a downstream agent discovers the input is incomplete — e.g., the implementation-planner finds the architecture can't be decomposed incrementally.
- **The context-engineer operates orthogonally** — it can be invoked at any point to audit or improve context artifacts, independent of the pipeline.

### Parallel Execution

Launch independent agents concurrently whenever possible:

```
# GOOD — parallel when independent
Launch in parallel:
  1. researcher: investigate authentication library options
  2. researcher: audit current database schema patterns

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

### Multi-Perspective Analysis

For complex or high-risk decisions, use parallel agents with distinct review lenses:

- **Correctness reviewer** — does the design satisfy requirements?
- **Security reviewer** — does the design introduce vulnerabilities?
- **Performance reviewer** — does the design introduce bottlenecks?
- **Maintainability reviewer** — can the team evolve this over time?

Reserve multi-perspective analysis for decisions with significant blast radius. Most tasks need only the standard pipeline.

### Boundary Discipline

Each agent has a defined responsibility — respect the boundaries:

- **Researcher does not recommend.** It presents options with trade-offs.
- **Architect does not plan steps.** It designs structure and makes decisions.
- **Implementation planner does not redesign.** It decomposes and supervises.
- **Context engineer does not implement features.** It manages the information architecture.

When an agent encounters work outside its boundary, it flags the need and recommends invoking the appropriate agent.

### Agent Selection Criteria

When deciding whether to use an agent vs. doing the work directly:

| Situation | Agent | Direct |
|-----------|-------|--------|
| Multi-source research with synthesis needed | Agent | — |
| Quick lookup in one file | — | Direct |
| Architecture affecting 3+ components | Agent | — |
| Simple function addition with clear placement | — | Direct |
| Breaking a large feature into incremental steps | Agent | — |
| One-step obvious change | — | Direct |

**Rule of thumb:** If the task benefits from a separate context window (large scope, multiple phases, structured output), use an agent. If it fits in the current conversation, work directly.

### Background Agents

Run agents in the background when their output is not immediately needed:

- Research tasks that will inform a later decision
- Context audits alongside active development
- Parallel investigation of independent concerns

Check background agent output before proceeding with work that depends on their findings.
