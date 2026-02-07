# ai-assistants

Configuration repository for AI coding assistants. The goal is to centralize and version-control settings, skills, commands, and agents across different AI tools (Claude Code, Claude Desktop, Cursor, ChatGPT, etc.), sharing reusable pieces where possible.

## Status

Early stage. Currently targeting **Claude Code** and **Claude Desktop** only.

## Structure

- `skills/` — Shared skill modules (assistant-agnostic)
- `commands/` — Shared slash commands
- `agents/` — Shared agent definitions (`researcher`, `systems-architect`, `implementation-planner`, `context-engineer`)
- `rules/` — Rules installed to `~/.claude/rules/` (auto-loaded by Claude when relevant)
  - `swe/coding-style.md` — Language-independent structural and design conventions
  - `swe/software-agents-usage.md` — Agent selection, coordination pipeline, parallel execution, and boundary discipline
  - `swe/vcs/git-commit-message-format.md` — Commit message format and type prefixes
  - `swe/vcs/git-commit-hygiene.md` — Git commit safety, staging discipline, and exclusions
  - `writing/readme-style.md` — Precision-first technical writing style for README.md files
- `.claude-plugin/` — Claude Code plugin manifest (`i-am`) and marketplace (`bit-agora`)
  - `plugin.json` — Plugin name, version, component paths
  - `PLUGIN_SCHEMA_NOTES.md` — Validator constraints reference
- `.claude/` — Claude personal config (symlinked to `~/.claude/`)
  - `CLAUDE.md` — Global development guidelines
  - `claude_desktop_config.json` — Claude Desktop settings (MCP servers)
  - `userPreferences.txt` — Adaptive precision mode instructions
  - `settings.local.json` — Local permission settings
- `install.sh` — Multi-assistant installer (`--claude` default, prompts for plugin)

## Working on this Repo

- When adding or modifying skills, load the `skill-crafting` skill for spec compliance
- When adding or modifying commands, load the `command-crafting` skill
- When adding or modifying agents, load the `agent-crafting` skill
- When adding or modifying rules, load the `rule-crafting` skill
- Follow commit conventions in `rules/` (auto-loaded by Claude when relevant)
- **Never modify `~/.claude/plugins/cache/`** — it contains installed copies that get overwritten on reinstall; always edit source files in this repo instead
- See `README.md` for full project documentation and `skills/README.md` for the skill catalog

## Design Intent

- **Shared assets at the root**: `skills/`, `commands/`, `agents/` are assistant-agnostic
- **Assistant-specific config in subdirectories**: `.claude/` for Claude, future `.chatgpt/` etc.
- **Plugin distribution**: Skills, commands, and agents installed via Claude Code plugin system
- **Personal config via symlinks**: `install.sh` symlinks `.claude/` files to `~/.claude/`
- Skills use progressive disclosure: metadata at startup, full content on activation, reference files on demand
