# Claude Agents

Custom agents for specialized workflows. Agents are autonomous subprocesses that Claude spawns to handle complex, multi-step tasks in a separate context window.

## Available Agents

### Software Development Crew

Seven agents that collaborate on software development tasks, each with a dedicated responsibility. They communicate through shared documents and can be invoked independently or in sequence. The promethean sits upstream as an optional ideation engine. The context-engineer can engage at any pipeline stage as a domain expert when the work involves context artifacts. The implementer executes plan steps with skill-augmented coding. The verifier sits downstream as an optional quality gate.

```
 promethean ──► IDEA_PROPOSAL.md (optional — when ideation is needed)
     │
     ▼
 researcher ──► RESEARCH_FINDINGS.md
     │                              ┌─────────────────┐
     ▼                              │ context-engineer │
 systems-architect ──► SYSTEMS_PLAN.md  │  (domain expert  │
     │                              │   at any stage)  │
     ▼                              └─────────────────┘
 implementation-planner ──► IMPLEMENTATION_PLAN.md (Steps), WIP.md, LEARNINGS.md
     │
     ▼
 implementer ───────────► code changes + WIP.md status (sequential or parallel)
     │
     ▼
 verifier ──────────────► VERIFICATION_REPORT.md (optional — when quality review needed)
```

| Agent | Description | Skills Used |
|-------|-------------|-------------|
| `promethean` | Analyzes project state, generates feature-level improvement ideas through dialog, and writes `IDEA_PROPOSAL.md` for downstream agents | — |
| `researcher` | Explores codebases, gathers external documentation, evaluates alternatives, and distills findings into `RESEARCH_FINDINGS.md` | — |
| `systems-architect` | Evaluates trade-offs, assesses codebase readiness, and produces architectural decisions in `SYSTEMS_PLAN.md` | — |
| `implementation-planner` | Breaks architecture into incremental steps (`IMPLEMENTATION_PLAN.md`, `WIP.md`, `LEARNINGS.md`) and supervises execution | `software-planning` |
| `context-engineer` | Audits, architects, and optimizes context artifacts (CLAUDE.md, skills, rules, commands, agents); collaborates with pipeline agents as domain expert for context engineering; implements context artifacts directly or under planner supervision | `skill-crafting`, `rule-crafting`, `command-crafting`, `agent-crafting` |
| `implementer` | Implements individual plan steps with skill-augmented coding, self-reviews against conventions, and reports completion. Supports sequential and parallel execution | `software-planning`, `code-review`, `refactoring` |
| `verifier` | Verifies completed implementation against acceptance criteria, coding conventions, and test coverage; produces `VERIFICATION_REPORT.md` with pass/fail/warn findings | `code-review` |

## How Agents Work

Agents are **delegated, not invoked**. Claude decides when to spawn an agent based on the task at hand and the agent's `description` field. Unlike skills and commands, agents don't have a `/slash-command` syntax.

- Each agent runs in its own context window with its own tool permissions
- Agents cannot spawn other agents
- Skills listed in the agent's `skills` field are injected into its context (agents do not inherit skills from the parent)
- Foreground agents block the main conversation; background agents run concurrently

## Using Agents

### In conversation (recommended)

Ask Claude directly — it delegates based on the agent's description:

```
"Use the researcher agent to investigate authentication libraries"
"Run the systems-architect to design the new API layer"
```

### `/agents` command

List all available agents (built-in, user, project, and plugin):

```
/agents
```

### `--agent` flag (run as main thread)

Run Claude *as* a specific agent for the entire session. This makes the agent the main thread, not a delegated subagent — useful for headless or scripted runs:

```bash
claude --agent i-am:researcher -p "investigate X"
```

### `--agents` JSON flag (session-only overrides)

Define or override agents dynamically for a single session:

```bash
claude --agents '{
  "researcher": {
    "description": "Research specialist",
    "prompt": "You are a researcher...",
    "tools": ["Read", "Grep", "Glob", "Bash", "WebSearch", "WebFetch"],
    "skills": ["python-development"]
  }
}'
```

### Priority order

When multiple agents share the same name, higher priority wins:

| Location | Priority |
|----------|----------|
| `--agents` CLI flag | 1 (highest) |
| `.claude/agents/` (project) | 2 |
| `~/.claude/agents/` (user) | 3 |
| Plugin `agents/` | 4 (lowest) |

## Plugin Registration

Agents require explicit file paths in `plugin.json` (directory wildcards are not supported):

```json
"agents": [
  "./agents/promethean.md",
  "./agents/researcher.md",
  "./agents/systems-architect.md",
  "./agents/implementation-planner.md",
  "./agents/context-engineer.md",
  "./agents/verifier.md",
  "./agents/implementer.md"
]
```

---

For creating custom agents, see the `agent-crafting` skill documentation.
