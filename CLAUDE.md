# ai-assistants

Configuration repository for AI coding assistants. The goal is to centralize and version-control settings, skills, commands, and agents across different AI tools (Claude Code, Claude Desktop, Cursor, ChatGPT, etc.), sharing reusable pieces where possible.

## Status

Early stage. Currently targeting **Claude Code** and **Claude Desktop** only.

## Structure

- `.claude/` — Claude-specific configuration (symlinked to `~/.claude/` via `install.sh`)
  - `CLAUDE.md` — Global development guidelines (shared across all projects)
  - `skills/` — Reusable skills for Claude Code
  - `commands/` — Slash commands (`/co`, `/cop`, `/create_worktree`, etc.)
  - `agents/` — Custom subagent definitions
  - `claude_desktop_config.json` — Claude Desktop settings
  - `commit-conventions.md` — Commit message conventions
- `install.sh` — Symlinks `.claude/` contents to `~/.claude/` and Claude Desktop config path

## Design Intent

- Assistant-specific config lives in its own directory (e.g., `.claude/` for Claude)
- Shared/reusable assets (skills, prompts, conventions) should be extractable so multiple assistants can reference them
- `install.sh` handles the symlinking for Claude; other assistants will get their own setup as needed
