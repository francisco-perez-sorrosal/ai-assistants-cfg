# Project Index

Last updated: 2026-02-07

## Inventory

Configuration repository for AI coding assistants. Centralizes settings, skills, commands, and agents for Claude Code (primary target).

### Skills (9)

| Skill | Purpose |
|-------|---------|
| skill-crafting | Creating and optimizing Agent Skills |
| agent-crafting | Building custom agents with prompts, tools, lifecycle hooks |
| command-crafting | Creating slash commands with arguments and tool permissions |
| rule-crafting | Creating rules — contextual domain knowledge files |
| mcp-crafting | Building MCP servers in Python with FastMCP |
| python | Modern Python development conventions |
| python-prj-mgmt | Python project management with pixi and uv |
| refactoring | Pragmatic refactoring: modularity, coupling, cohesion |
| software-planning | Three-document planning model (PLAN.md, WIP.md, LEARNINGS.md) |

### Agents (5)

| Agent | Purpose |
|-------|---------|
| promethean | Feature-level ideation from project state analysis |
| researcher | Codebase exploration, external docs, comparative analysis |
| systems-architect | Trade-off analysis, codebase readiness, system design |
| implementation-planner | Step decomposition, execution supervision |
| context-engineer | Context artifact auditing, architecture, and optimization |

### Commands (7)

| Command | Purpose |
|---------|---------|
| co | Create a commit for staged (or all) changes |
| cop | Create a commit and push to remote |
| create-worktree | Create a new git worktree in .trees/ |
| merge-worktree | Merge a worktree branch back into current branch |
| create-simple-python-prj | Create a basic Python project with pixi or uv |
| add-rules | Copy rules into the current project for customization |
| manage-readme | Create or refine README.md files |

### Rules (6)

| Rule | Purpose |
|------|---------|
| swe/coding-style.md | Language-independent structural and design conventions |
| swe/software-agents-usage.md | When and how to use the available software agents |
| swe/agent-intermediate-documents.md | Placement and lifecycle of agent pipeline documents |
| swe/vcs/git-commit-hygiene.md | Git commit safety and hygiene |
| swe/vcs/git-commit-message-format.md | Commit message structure and type prefixes |
| writing/readme-style.md | Technical writing conventions for README files |

## Idea Ledger

### Implemented

- **Ecosystem consistency audit** (2026-02-07) — Audited all crafting skills against their governed artifacts. Fixed 2 critical YAML bugs, 5 stale catalogs, and 13 consistency improvements across specs and artifacts.

### Pending

(none)

### Discarded

(none)

## Future Paths

Directional possibilities for where the project could go. Paths may be compatible or mutually exclusive — this section maps the option space, not a single roadmap.

- **Multi-assistant expansion** — Extend beyond Claude Code to Cursor, ChatGPT, and other assistants. Would require abstracting assistant-specific config into adapter layers while keeping shared assets (skills, commands, agents) portable.
- **Community plugin ecosystem** — Evolve from personal config repo to a distributable plugin marketplace with versioning, dependency management, and discovery.
- **Project template generation** — Use the accumulated skills and rules as a foundation for scaffolding new projects with pre-configured AI assistant setups.
