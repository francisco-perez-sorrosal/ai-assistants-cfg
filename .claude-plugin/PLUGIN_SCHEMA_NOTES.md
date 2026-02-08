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
