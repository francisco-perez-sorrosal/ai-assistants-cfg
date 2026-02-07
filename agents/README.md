# Claude Agents

Custom agents for specialized workflows. Agents are autonomous subprocesses that Claude spawns to handle complex, multi-step tasks in a separate context window.

## Available Agents

### Software Development Crew

Three agents that collaborate on software development tasks, each with a dedicated responsibility. They communicate through shared documents and can be invoked independently or in sequence.

```
User Request
     │
     ▼
 researcher ──► RESEARCH_FINDINGS.md
     │
     ▼
 systems-architect ──► SYSTEMS_PLAN.md (Goal, Criteria, Architecture, Risks)
     │
     ▼
 implementation-planner ──► IMPLEMENTATION_PLAN.md (Steps), WIP.md, LEARNINGS.md
```

| Agent | Description | Skills Used |
|-------|-------------|-------------|
| `researcher` | Explores codebases, gathers external documentation, evaluates alternatives, and distills findings into `RESEARCH_FINDINGS.md` | — |
| `systems-architect` | Evaluates trade-offs, assesses codebase readiness, and produces architectural decisions in `SYSTEMS_PLAN.md` | — |
| `implementation-planner` | Breaks architecture into incremental steps (`IMPLEMENTATION_PLAN.md`, `WIP.md`, `LEARNINGS.md`) and supervises execution | `software-planning` |

### Context Engineering

| Agent | Description | Skills Used |
|-------|-------------|-------------|
| `context-engineer` | Audits, architects, and optimizes AI assistant context artifacts (CLAUDE.md, skills, rules, commands, agents) for quality, consistency, and token efficiency | `skill-crafting`, `rule-crafting`, `command-crafting`, `agent-crafting` |

## How Agents Work

Agents are **delegated, not invoked**. Claude decides when to spawn an agent based on the task at hand and the agent's description. Agents can also be triggered explicitly by name.

- Each agent runs in its own context window with its own tool permissions
- Agents cannot spawn other agents
- Skills listed in the agent's `skills` field are injected into its context (agents do not inherit skills from the parent)
- Foreground agents block the main conversation; background agents run concurrently

## Plugin Registration

Agents require explicit file paths in `plugin.json` (directory wildcards are not supported):

```json
"agents": [
  "./agents/researcher.md",
  "./agents/systems-architect.md",
  "./agents/implementation-planner.md",
  "./agents/context-engineer.md"
]
```

---

For creating custom agents, see the `agent-crafting` skill documentation.
