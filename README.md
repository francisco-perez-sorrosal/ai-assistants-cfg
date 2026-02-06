# ai-assistants

Configuration repository for AI coding assistants. Centralizes and version-controls settings, skills, commands, and agents across different AI tools, sharing reusable pieces where possible.

**Status**: Early stage — currently targeting **Claude Code** and **Claude Desktop** only.

## Structure

```
skills/                              # Shared skill modules (assistant-agnostic)
├── skill-crafting/                  # Creating and maintaining skills
├── agent-crafting/                  # Building custom agents/subagents
├── command-crafting/                # Creating slash commands
├── mcp-crafting/                    # Building MCP servers in Python
├── python/                          # Python development best practices
├── python-prj-mgmt/                # Project setup with pixi/uv
├── refactoring/                     # Code restructuring patterns
├── software-planning/               # Three-document planning model
├── stock-clusters/                  # Stock clustering analysis
└── ticker/                          # Stock ticker lookup
commands/                            # Shared slash commands
├── co.md                            # /co — commit staged changes
├── cop.md                           # /cop — commit and push
├── create_worktree.md               # /create_worktree — new git worktree
├── merge_worktree.md                # /merge_worktree — merge worktree branch
└── create-simple-python-prj.md      # /create-simple-python-prj — scaffold project
agents/                              # Shared agent definitions (none yet)
rules/                               # Rules (installed to ~/.claude/rules/)
├── git-commit-message-format.md     # Commit message format and type prefixes
└── git-commit-rules.md              # Git commit safety and hygiene rules
.claude-plugin/                      # Claude Code plugin manifest
├── plugin.json
└── PLUGIN_SCHEMA_NOTES.md
.claude/                             # Claude personal config (symlinked to ~/.claude/)
├── CLAUDE.md                        # Global development guidelines
├── claude_desktop_config.json       # Claude Desktop settings (MCP servers)
├── userPreferences.txt              # Adaptive precision mode instructions
└── settings.local.json              # Local permission settings (gitignored)
install.sh                           # Multi-assistant installer
```

## Installation

### Plugin (skills, commands, agents)

The repo is packaged as a Claude Code plugin (`i-am`) distributed via the `bit-agora` marketplace. Install via the `/plugin` command or CLI:

```bash
# Load directly for a single session (no install needed)
claude --plugin-dir /path/to/ai-assistants

# Or add as a marketplace and install persistently
claude plugin marketplace add /path/to/ai-assistants
claude plugin install i-am@bit-agora
```

When installed as a plugin, commands are namespaced: `/co` becomes `/i-am:co`.

Use `claude plugin validate .` from the repo root to verify the plugin structure.

### Personal config (`install.sh`)

Run `./install.sh` to symlink Claude personal config files to `~/.claude/` and install rules. The installer also prompts to install the `i-am` plugin via the marketplace.

```bash
./install.sh          # Install Claude personal config (prompts for plugin)
./install.sh --help   # Show all options
```

**What gets installed:**


| Source (`.claude/`)          | Target (`~/.claude/`)                   | Purpose                                                                  |
| ---------------------------- | --------------------------------------- | ------------------------------------------------------------------------ |
| `CLAUDE.md`                  | `~/.claude/CLAUDE.md`                   | Global development guidelines, code style, available skills and commands |
| `claude_desktop_config.json` | `~/.claude/claude_desktop_config.json`  | Claude Desktop settings (MCP servers)                                    |
| `userPreferences.txt`        | `~/.claude/userPreferences.txt`         | Adaptive precision mode — controls response style and verbosity          |
| `settings.local.json`        | `~/.claude/settings.local.json`         | Local permission settings (gitignored)                                   |
| `rules/*.md`                      | `~/.claude/rules/*.md`                      | Rules (auto-linked, auto-loaded by Claude when relevant)           |


The installer also links `claude_desktop_config.json` to the official Claude Desktop location:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### User preferences on Claude Desktop / iOS

On devices without filesystem access (e.g., Claude iOS app) or when using Claude Desktop without the CLI, you can load the same user preferences by pasting the following into the **User Preferences** field in Claude's settings:

```
Read the user preferences from https://raw.githubusercontent.com/francisco-perez-sorrosal/ai-assistants-cfg/main/.claude/userPreferences.txt and follow them before any other interaction
```

This tells Claude to fetch and apply the adaptive precision mode instructions at the start of each conversation, keeping behavior consistent across all clients.

## Skills

Reusable knowledge modules that Claude loads automatically based on context. See `[skills/README.md](skills/README.md)` for the full catalog.

**Categories**: AI assistant crafting (skill-crafting, agent-crafting, command-crafting, mcp-crafting) · Software development (python, python-prj-mgmt, refactoring, software-planning) · Domain-specific (stock-clusters, ticker)

## Commands

Slash commands invoked with `/<name>` in Claude Code. When installed as a plugin, commands are namespaced as `/i-am:<name>`.


| Command                                                   | Description                                         |
| --------------------------------------------------------- | --------------------------------------------------- |
| `/co`                                                     | Create a commit for staged (or all) changes         |
| `/cop`                                                    | Create a commit and push to remote                  |
| `/create_worktree [branch]`                               | Create a new git worktree in `.trees/`              |
| `/merge_worktree [branch]`                                | Merge a worktree branch back into current branch    |
| `/create-simple-python-prj [name] [desc] [pkg-mgr] [dir]` | Scaffold a Python project (defaults: pixi, `~/dev`) |


## Design Intent

- **Assistant-agnostic shared assets**: `skills/`, `commands/`, `agents/` live at the repo root, reusable across any AI assistant
- **Assistant-specific config**: Personal settings live in assistant directories (`.claude/` for Claude, future `.chatgpt/` etc.)
- **Plugin distribution**: Skills, commands, and agents are installed via Claude Code's plugin system (`.claude-plugin/plugin.json`)
- **Symlink for personal config**: `install.sh` symlinks assistant-specific config to the expected locations
- **Progressive disclosure**: Skills load metadata at startup, full content on activation, reference files on demand

## References

- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
- [Claude Code Sub-agents](https://code.claude.com/docs/en/sub-agents)
- [Agent Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices.md)
- [bendrucker/claude config](https://github.com/bendrucker/claude/blob/main/.claude/)
- [citypaul/.dotfiles claude config](https://github.com/citypaul/.dotfiles/blob/main/claude)

