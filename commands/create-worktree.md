---
description: Create a new git worktree in .trees/
argument-hint: [branch-name]
allowed-tools: [Bash(git:*), Bash(ln:*), Bash(ls:*), Bash(cursor:*)]
---

Create a new worktree named .trees/$ARGUMENTS.

## Steps

1. Check if `.trees/$ARGUMENTS` already exists. If it does, stop and tell the user the worktree already exists
2. Create a new git worktree in the `.trees/` folder with the name `$ARGUMENTS`
3. Symlink the `.venv` folder into the worktree directory
4. Launch the user's editor in that directory (try `cursor` first; if unavailable, try `code`; if neither is found, print the worktree path for the user to open manually)
