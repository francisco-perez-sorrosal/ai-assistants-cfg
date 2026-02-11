# ai-assistants

Configuration repository for AI coding assistants. The goal is to centralize and version-control settings, skills, commands, and agents across different AI tools (Claude Code, Claude Desktop, Cursor, ChatGPT, etc.), sharing reusable pieces where possible.

## Status

Early stage. Currently targeting **Claude Code** and **Claude Desktop** only.

## Structure

- `skills/` — Shared skill modules (assistant-agnostic)
- `commands/` — Shared slash commands
- `agents/` — Shared agent definitions
- `rules/` — Rules installed to `~/.claude/rules/` (auto-loaded unconditionally by Claude)
- `.claude-plugin/` — Claude Code plugin manifest (`i-am`)
  - `plugin.json` — Plugin name, version, component paths
  - `PLUGIN_SCHEMA_NOTES.md` — Validator constraints reference
- `.claude/` — Claude personal config (symlinked to `~/.claude/`)
  - `CLAUDE.md` — Global development guidelines
  - `claude_desktop_config.json` — Claude Desktop settings (MCP servers)
  - `userPreferences.txt` — Adaptive precision mode instructions
  - `settings.local.json` — Local permission settings
- `task-chronograph-mcp/` — Pipeline observability MCP server (agent lifecycle, interactions, dashboard)
- `install.sh` — Multi-assistant installer (`--claude` default, prompts for plugin)

## Working on this Repo

- When adding or modifying skills, load the `skill-crafting` skill for spec compliance
- When adding or modifying commands, load the `command-crafting` skill
- When adding or modifying agents, load the `agent-crafting` skill
- When adding or modifying rules, load the `rule-crafting` skill
- Follow commit conventions in `rules/` (auto-loaded by Claude when relevant)
- **Never modify `~/.claude/plugins/cache/`** — it contains installed copies that get overwritten on reinstall; always edit source files in this repo instead
- **Token budget**: Always-loaded content (CLAUDE.md files + rules) must stay under 8,500 tokens (~29,750 chars). Before adding a new rule, verify the budget. Prefer skills with reference files for procedural content; reserve rules for declarative domain knowledge
- See `README.md` for user-facing documentation, `README_DEV.md` for contributor conventions, and `skills/README.md` for the skill catalog
- **Session memory**: At the start of each session, call the `session_start` memory MCP tool to load context about the user, project conventions, and past learnings. If `memories.assistant.name` is missing, pick a random name and call `remember` to store it immediately. Use the memory MCP tools proactively to store discoveries during the session. Be curious about the user -- learn their interests, background, and working style over time

## Design Intent

- **Shared assets at the root**: `skills/`, `commands/`, `agents/` are assistant-agnostic
- **Assistant-specific config in subdirectories**: `.claude/` for Claude, future `.chatgpt/` etc.
- **Plugin distribution**: Skills, commands, and agents installed via Claude Code plugin system
- **Personal config via symlinks**: `install.sh` symlinks `.claude/` files to `~/.claude/`
- Skills use progressive disclosure: metadata at startup, full content on activation, reference files on demand
- **Do not list skills, commands, agents, or rules in CLAUDE.md** — Claude auto-discovers all of them via filesystem scanning (plugin directories, `~/.claude/rules/`). Enumerating them in always-loaded context wastes tokens and creates sync burden. The `README.md` and per-directory READMEs serve as human-facing catalogs instead
