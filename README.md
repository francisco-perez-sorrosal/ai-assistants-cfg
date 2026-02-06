# ai-assistants

Configuration repository for AI coding assistants. Centralizes and version-controls settings, skills, commands, and agents across different AI tools, sharing reusable pieces where possible.

**Status**: Early stage — currently targeting **Claude Code** and **Claude Desktop** only.

## Structure

```
.claude/
├── CLAUDE.md                       # Global development guidelines
├── claude_desktop_config.json      # Claude Desktop settings (MCP servers, preferences)
├── commit-conventions.md           # Git commit message conventions
├── userPreferences.txt             # Adaptive precision mode instructions
├── settings.local.json             # Local permission settings
├── skills/                         # Reusable skill modules (8 skills)
│   ├── agent-skills/               # Creating and maintaining skills
│   ├── agent-creator/              # Building custom agents/subagents
│   ├── slash-cmd/                  # Creating slash commands
│   ├── python/                     # Python development best practices
│   ├── python-prj-mgmt/           # Project setup with pixi/uv
│   ├── refactoring/                # Code restructuring patterns
│   ├── software-planning/          # Three-document planning model
│   ├── stock-clusters/             # Stock clustering analysis
│   └── ticker/                     # Stock ticker lookup
├── commands/                       # Slash commands
│   ├── co.md                       # /co — commit staged changes
│   ├── cop.md                      # /cop — commit and push
│   ├── create_worktree.md          # /create_worktree — new git worktree
│   ├── merge_worktree.md           # /merge_worktree — merge worktree branch
│   └── create-simple-python-prj.md # /create-simple-python-prj — scaffold project
└── agents/                         # Custom agent definitions (none yet)
install.sh                          # Symlinks .claude/ to ~/.claude/
```

## Installation

Run `./install.sh` to symlink the `.claude/` directory contents to `~/.claude/`.

The installer prompts before overwriting existing files and also links `claude_desktop_config.json` to the official Claude Desktop location:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

This creates a symlink chain: `<official location>` → `~/.claude/claude_desktop_config.json` → `<project>/.claude/claude_desktop_config.json`, keeping everything version-controlled.

## Skills

Reusable knowledge modules that Claude loads automatically based on context. See [`.claude/skills/README.md`](.claude/skills/README.md) for the full catalog.

**Categories**: Claude Code authoring (agent-skills, agent-creator, slash-cmd) · Software development (python, python-prj-mgmt, refactoring, software-planning) · Domain-specific (stock-clusters, ticker)

## Commands

Slash commands invoked with `/<name>` in Claude Code:

| Command | Description |
|---------|-------------|
| `/co` | Create a commit for staged (or all) changes |
| `/cop` | Create a commit and push to remote |
| `/create_worktree [branch]` | Create a new git worktree in `.trees/` |
| `/merge_worktree [branch]` | Merge a worktree branch back into current branch |
| `/create-simple-python-prj [name] [desc] [pkg-mgr] [dir]` | Scaffold a Python project (defaults: pixi, `~/dev`) |

## Design Intent

- Assistant-specific config lives in its own directory (`.claude/` for Claude)
- Shared/reusable assets (skills, prompts, conventions) are extractable so multiple assistants can reference them
- `install.sh` handles symlinking for Claude; other assistants will get their own setup as needed
- Skills use progressive disclosure: metadata loaded at startup, full content on activation, reference files on demand

## References

- [Claude Code Sub-agents](https://code.claude.com/docs/en/sub-agents)
- [Agent Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices.md)
- [bendrucker/claude config](https://github.com/bendrucker/claude/blob/main/.claude/)
- [citypaul/.dotfiles claude config](https://github.com/citypaul/.dotfiles/blob/main/claude)
