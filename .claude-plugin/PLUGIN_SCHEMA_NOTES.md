# Plugin Manifest Schema Notes

Undocumented but strict constraints enforced by the Claude Code plugin validator. Sourced from [everything-claude-code](https://github.com/affaan-m/everything-claude-code/tree/main/.claude-plugin).

## Component Fields Must Be Arrays

`commands`, `skills`, and `agents` must always be arrays, never strings:

```json
"commands": ["./.claude/commands/"]   // correct
"commands": "./.claude/commands/"     // fails on marketplace install
```

## Agents Require Explicit File Paths

Directory paths are rejected for agents. Enumerate each file:

```json
"agents": ["./agents/planner.md", "./agents/reviewer.md"]   // correct
"agents": ["./agents/"]                                       // fails
```

## Plugin Hooks Do NOT Auto-Fire

Despite claims in third-party sources, placing `hooks/hooks.json` inside `.claude-plugin/` does **not** cause Claude Code to auto-discover and execute those hooks (tested in v2.1.37). The file is installed into the plugin cache but never invoked.

**Workaround:** Define hooks in project-level `.claude/settings.local.json` (or `settings.json`) with absolute paths to the hook scripts. The plugin's `hooks.json` is retained as a reference for what hooks are available, but does not activate them.

**`${CLAUDE_PLUGIN_ROOT}` resolution:** When used in plugin hooks, this variable resolves to the installed plugin's root directory in the cache (e.g., `~/.claude/plugins/cache/bit-agora/i-am/0.0.1/`), NOT to the `.claude-plugin/` subdirectory. Scripts at `.claude-plugin/hooks/send_event.py` would need to be referenced as `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/hooks/send_event.py`.

## Do Not Declare Hooks in plugin.json

Adding `"hooks"` to the manifest causes a duplicate file error. The hooks config lives separately in `hooks/hooks.json` within the `.claude-plugin/` directory.

## mcpServers Auto-Registers MCP Servers

The `mcpServers` key in `plugin.json` registers MCP servers automatically when the plugin loads. Format matches Claude Desktop config — **only stdio transport is supported** (`command` + `args`). There is no `url` field for HTTP transport.

```json
"mcpServers": {
  "server-name": {
    "command": "uv",
    "args": ["run", "--project", "${CLAUDE_PLUGIN_ROOT}/subdir", "python", "-m", "my_module"]
  }
}
```

Reference: [claude-mermaid](https://github.com/veelenga/claude-mermaid/tree/main/.claude-plugin) uses this for npm-based MCP servers. For Python projects, `uv run --project` handles dependency installation on first launch.

**Hybrid stdio+HTTP pattern:** Since only stdio is supported, a server that also needs HTTP (e.g., for a web dashboard) can start an HTTP server in a daemon thread before entering the stdio transport. The `task-chronograph` server uses this approach — its `__main__.py` launches uvicorn in a background thread, then calls `mcp.run()` on stdio. The plugin registers the stdio transport; the HTTP dashboard comes as a side effect. See `task-chronograph-mcp/README.md` for details.

**Note:** `${CLAUDE_PLUGIN_ROOT}` resolution in `mcpServers` args is assumed based on its behavior in hook commands — verify after plugin reinstall.

## Version Field Is Mandatory

Omitting `version` causes installation failures during marketplace deployment.

## Validator Quirks

- Local validation may pass while marketplace installation fails
- Error messages are generic (e.g., `agents: Invalid input`) without indicating the root cause
- Prefer explicit file paths over directory paths when in doubt

## Pre-Edit Checklist

1. All component fields are arrays
2. Agents use explicit file paths (not directories)
3. `version` field is present
4. No `hooks` field in the manifest
5. Run `claude plugin validate .` from the repo root
