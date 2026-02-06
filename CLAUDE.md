# ai-assistants

Configuration repository for AI coding assistants. The goal is to centralize and version-control settings, skills, commands, and agents across different AI tools (Claude Code, Claude Desktop, Cursor, ChatGPT, etc.), sharing reusable pieces where possible.

## Status

Early stage. Currently targeting **Claude Code** and **Claude Desktop** only.

## Structure

- `.claude/` — Claude-specific configuration (symlinked to `~/.claude/` via `install.sh`)
  - `CLAUDE.md` — Global development guidelines (shared across all projects)
  - `skills/` — Reusable skill modules (authoring, development, and domain-specific categories)
  - `commands/` — Slash commands (`/co`, `/cop`, `/create_worktree`, `/merge_worktree`, `/create-simple-python-prj`)
  - `agents/` — Custom subagent definitions (none yet)
  - `claude_desktop_config.json` — Claude Desktop settings (MCP servers, preferences)
  - `commit-conventions.md` — Commit message conventions
  - `userPreferences.txt` — Adaptive precision mode instructions
  - `settings.local.json` — Local permission settings
- `install.sh` — Symlinks `.claude/` contents to `~/.claude/` and Claude Desktop config path

## Working on this Repo

- When adding or modifying skills, load the `agent-skills` skill for spec compliance
- When adding or modifying commands, load the `slash-cmd` skill
- When adding or modifying agents, load the `agent-creator` skill
- Follow commit conventions in `.claude/commit-conventions.md`
- See `README.md` for full project documentation and `skills/README.md` for the skill catalog

## Design Intent

- Assistant-specific config lives in its own directory (e.g., `.claude/` for Claude)
- Shared/reusable assets (skills, prompts, conventions) should be extractable so multiple assistants can reference them
- Skills use progressive disclosure: metadata at startup, full content on activation, reference files on demand
- `install.sh` handles the symlinking for Claude; other assistants will get their own setup as needed
