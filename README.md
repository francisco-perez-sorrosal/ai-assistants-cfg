# ai-assistants

Configuration repository for AI coding assistants. Centralizes settings, skills, commands, agents, and rules -- currently targeting **Claude Code** and **Claude Desktop**.

## Installation

Run the interactive installer — it walks through each choice, defaulting to the recommended option at each step.

```bash
./install.sh              # Claude Code (default)
./install.sh desktop      # Claude Desktop
./install.sh --check      # Verify installation health
./install.sh --uninstall  # Remove installation
```

### Claude Code (`./install.sh` or `./install.sh code`)

| Step | What | Interactive? |
|------|------|-------------|
| 1 | Personal config (CLAUDE.md, userPreferences.txt, settings.local.json) → `~/.claude/` | No — always installed |
| 2 | Rules → `~/.claude/rules/` (auto-loaded by Claude when relevant) | No — always installed |
| 3 | i-am plugin via [`bit-agora`](https://github.com/francisco-perez-sorrosal/bit-agora) marketplace (scope: user or project) | Yes — recommended |
| 4 | Task Chronograph hooks (agent lifecycle observability) | Yes — recommended |
| 5 | Claude Desktop config link to official Desktop location | Yes — skip by default |

When installed as a plugin, commands are namespaced: `/co` becomes `/i-am:co`. Plugin permissions for skill reference files are auto-configured at Step 3. See [`README_DEV.md`](README_DEV.md#progressive-disclosure-and-satellite-files) for how progressive disclosure works with plugin-installed skills.

**Manual plugin install** (without the interactive installer):

```bash
claude plugin marketplace add francisco-perez-sorrosal/bit-agora
claude plugin install i-am@bit-agora --scope user
```

### Claude Desktop (`./install.sh desktop`)

Links `claude_desktop_config.json` to the official Desktop location:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Skills, commands, and agents are Claude Code features — run `./install.sh code` for the full feature set.

### User preferences (Claude Desktop / iOS)

On devices without filesystem access (e.g., Claude iOS app) or when using Claude Desktop without the CLI, paste the following into the **User Preferences** field in Claude's settings:

```text
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

Domain knowledge files eagerly loaded by Claude within scope (personal rules for all projects, project rules for that project). See [`rules/README.md`](rules/README.md) for the full catalog, writing guidelines, and the rules-vs-skills-vs-CLAUDE.md decision model.

---

For contributor and developer documentation, see [`README_DEV.md`](README_DEV.md).
