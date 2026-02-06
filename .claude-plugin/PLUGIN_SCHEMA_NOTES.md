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

## Do Not Declare Hooks

Since v2.1+, `hooks/hooks.json` is auto-discovered by convention. Adding `"hooks"` to the manifest causes a duplicate file error.

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
