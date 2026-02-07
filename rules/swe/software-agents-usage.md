## Software Agent Usage

Conventions for when and how to use the available software agents — autonomous subprocesses that run in separate context windows.

### Available Agents

| Agent | Purpose | Output | When to Use |
|-------|---------|--------|-------------|
| `promethean` | Feature-level ideation from project state analysis | `IDEA_PROPOSAL.md` | Generating improvement ideas, exploring gaps, creative exploration of opportunities |
| `researcher` | Codebase exploration, external docs, comparative analysis | `RESEARCH_FINDINGS.md` | Understanding a technology, evaluating options, gathering context |
| `systems-architect` | Trade-off analysis, codebase readiness, system design | `SYSTEMS_PLAN.md` | Architectural decisions, structural assessment, technology selection |
| `implementation-planner` | Step decomposition, execution supervision | `IMPLEMENTATION_PLAN.md`, `WIP.md`, `LEARNINGS.md` | Breaking architecture into increments, resuming multi-session work |
| `context-engineer` | Context artifact domain expert and implementer — audits, architects, and optimizes context artifacts; collaborates at any pipeline stage when work involves context engineering | Audit report + artifact changes | Auditing quality, resolving conflicts, growing the context ecosystem, providing domain expertise during pipeline work involving context artifacts |

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

**Rule of thumb:** If the task benefits from a separate context window (large scope, multiple phases, structured output), use an agent. If it fits in the current conversation, work directly.

### Background Agents

Run agents in the background when their output is not immediately needed:

- Research tasks that will inform a later decision
- Context audits alongside active development
- Parallel investigation of independent concerns

Check background agent output before proceeding with work that depends on their findings.

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
