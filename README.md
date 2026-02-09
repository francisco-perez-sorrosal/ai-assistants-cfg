# ai-assistants

Configuration repository for AI coding assistants. Centralizes settings, skills, commands, agents, and rules -- currently targeting **Claude Code** and **Claude Desktop**.

## Installation

### Plugin (skills, commands, agents)

The repo is packaged as a Claude Code plugin (`i-am`) distributed via the [`bit-agora`](https://github.com/francisco-perez-sorrosal/bit-agora) marketplace.

```bash
# Add the marketplace and install
claude plugin marketplace add francisco-perez-sorrosal/bit-agora
claude plugin install i-am                    # user scope (all projects)
claude plugin install i-am --scope project    # project scope only
```

```bash
# Or load directly for a single session (no install needed)
claude --plugin-dir /path/to/ai-assistants
```

When installed as a plugin, commands are namespaced: `/co` becomes `/i-am:co`.

### Personal config

Run `./install.sh` to symlink Claude personal config files to `~/.claude/` and install rules. The installer also prompts to install the plugin via the marketplace.

```bash
./install.sh          # Install Claude config, prompt for plugin
./install.sh --help   # Show all options
```

### User preferences on Claude Desktop / iOS

On devices without filesystem access (e.g., Claude iOS app) or when using Claude Desktop without the CLI, paste the following into the **User Preferences** field in Claude's settings:

```
Read the user preferences from https://raw.githubusercontent.com/francisco-perez-sorrosal/ai-assistants-cfg/main/.claude/userPreferences.txt and follow them before any other interaction
```

This tells Claude to fetch and apply the adaptive precision mode instructions at the start of each conversation.

## Skills

Reusable knowledge modules loaded automatically based on context. See [`skills/README.md`](skills/README.md) for the full catalog.

| Category | Skills |
|----------|--------|
| AI Assistant Crafting | skill-crafting, agent-crafting, command-crafting, mcp-crafting, rule-crafting |
| Documentation | doc-management |
| Software Development | python-development, python-prj-mgmt, refactoring, code-review, software-planning |

## Commands

Slash commands invoked with `/<name>` in Claude Code. When installed as a plugin, use `/i-am:<name>`. See [`commands/README.md`](commands/README.md) for details.

| Command | Description |
|---------|-------------|
| `/add-rules [names... \| all]` | Copy rules into the current project for customization |
| `/co` | Create a commit for staged (or all) changes |
| `/cop` | Create a commit and push to remote |
| `/create-worktree [branch]` | Create a new git worktree in `.trees/` |
| `/merge-worktree [branch]` | Merge a worktree branch back into current branch |
| `/create-simple-python-prj [name] [desc] [pkg-mgr] [dir]` | Scaffold a Python project (defaults: pixi, `~/dev`) |
| `/manage-readme [file-paths...]` | Create or refine README.md files with precision-first style |

## Agents

Nine autonomous agents that Claude delegates complex tasks to. Each runs in its own context window with injected skills and scoped tool permissions. See [`agents/README.md`](agents/README.md) for the pipeline diagram and usage patterns.

| Agent | Description |
|-------|-------------|
| `promethean` | Feature-level ideation from project state |
| `researcher` | Codebase exploration, external docs, alternative evaluation |
| `systems-architect` | Trade-off analysis, system design |
| `implementation-planner` | Step decomposition, execution supervision |
| `context-engineer` | Context artifact auditing, optimization, ecosystem management |
| `implementer` | Step execution with skill-augmented coding and self-review |
| `verifier` | Post-implementation review against acceptance criteria |
| `doc-engineer` | Documentation quality management (READMEs, catalogs, changelogs) |
| `sentinel` | Independent ecosystem quality auditor |

## Rules

Contextual domain knowledge files loaded automatically by Claude when relevant. See [`rules/README.md`](rules/README.md) for the full catalog, writing guidelines, and the rules-vs-skills-vs-CLAUDE.md decision model.

---

For contributor and developer documentation, see [`README_DEV.md`](README_DEV.md).
