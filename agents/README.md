# Claude Agents

Custom agents for specialized workflows. Agents are autonomous subprocesses that Claude spawns to handle complex, multi-step tasks in a separate context window.

## Available Agents

| Agent | Description | Skills Used |
|-------|-------------|-------------|
| `software-architect` | Analyzes codebases, produces structured implementation plans, reviews through stakeholder lenses, and supervises execution (PLAN.md, WIP.md, LEARNINGS.md) | `software-planning` |

## How Agents Work

Agents are **delegated, not invoked**. Claude decides when to spawn an agent based on the task at hand and the agent's description. Agents can also be triggered explicitly by name.

- Each agent runs in its own context window with its own tool permissions
- Agents cannot spawn other agents
- Skills listed in the agent's `skills` field are injected into its context (agents do not inherit skills from the parent)
- Foreground agents block the main conversation; background agents run concurrently

## Plugin Registration

Agents require explicit file paths in `plugin.json` (directory wildcards are not supported):

```json
"agents": ["./agents/software-architect.md"]
```

---

For creating custom agents, see the `agent-crafting` skill documentation.
