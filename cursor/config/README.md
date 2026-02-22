# Cursor installer config

Resources used by `install_cursor.sh` (and the main installer when targeting Cursor).

- **mcp.json.template** — Template for `.cursor/mcp.json`. Placeholders are replaced at install time:
  - `{{MCP_ROOT}}` — Repo root (or `CURSOR_REPO_ROOT`) used for task-chronograph and memory MCP paths.
  - `{{AGENTS_DIR_ABS}}` — Absolute path to this repo’s `agents/` (for sub-agents-mcp).
  - `{{MEMORY_FILE}}` — Path for memory MCP state file (default: `.ai-state/memory.json`).

- **expected-mcp-servers.txt** — One server name per line. Used by `--check` to verify that `mcp.json` contains these MCP servers.

- **export-cursor-rules.py** — Exports `rules/*.md` to `.cursor/rules/` with Cursor frontmatter (`description`, `alwaysApply`). Invoked by `install_cursor.sh` with `repo_root` and `out_dir`.

- **export-cursor-commands.py** — Exports `commands/*.md` to `.cursor/commands/` (frontmatter stripped to plain Markdown). Invoked by `install_cursor.sh` with `repo_root` and `out_dir`.
