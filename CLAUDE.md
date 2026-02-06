# ai-assistants

Configuration repository for AI coding assistants. The goal is to centralize and version-control settings, skills, commands, and agents across different AI tools (Claude Code, Claude Desktop, Cursor, ChatGPT, etc.), sharing reusable pieces where possible.

## Status

Early stage. Currently targeting **Claude Code** and **Claude Desktop** only.

## Structure

- `skills/` — Shared skill modules (assistant-agnostic)
- `commands/` — Shared slash commands
- `agents/` — Shared agent definitions (none yet)
- `commit-conventions.md` — Git commit conventions (used by `/co` and `/cop` commands; also installed as a rule to `~/.claude/rules/`)
- `.claude-plugin/` — Claude Code plugin manifest (`fps-claude`)
  - `plugin.json` — Plugin name, version, component paths
  - `PLUGIN_SCHEMA_NOTES.md` — Validator constraints reference
- `.claude/` — Claude personal config (symlinked to `~/.claude/`)
  - `CLAUDE.md` — Global development guidelines
  - `claude_desktop_config.json` — Claude Desktop settings (MCP servers)
  - `userPreferences.txt` — Adaptive precision mode instructions
  - `settings.local.json` — Local permission settings
- `install.sh` — Multi-assistant installer (`--claude` default, `--with-plugin`)

## Working on this Repo

- When adding or modifying skills, load the `agent-skills` skill for spec compliance
- When adding or modifying commands, load the `slash-cmd` skill
- When adding or modifying agents, load the `agent-creator` skill
- Follow commit conventions in `commit-conventions.md`
- See `README.md` for full project documentation and `skills/README.md` for the skill catalog

## Design Intent

- **Shared assets at the root**: `skills/`, `commands/`, `agents/` are assistant-agnostic
- **Assistant-specific config in subdirectories**: `.claude/` for Claude, future `.chatgpt/` etc.
- **Plugin distribution**: Skills, commands, and agents installed via Claude Code plugin system
- **Personal config via symlinks**: `install.sh` symlinks `.claude/` files to `~/.claude/`
- Skills use progressive disclosure: metadata at startup, full content on activation, reference files on demand
