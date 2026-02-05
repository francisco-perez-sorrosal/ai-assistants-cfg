---
description: Merge a worktree branch back into current branch
argument-hint: [branch-name]
allowed-tools: [Bash(git:*), Read, Grep]
---

Merge the $ARGUMENTS worktree from `.trees/$ARGUMENTS` into the current branch.

## Steps

1. Change into the `.trees/$ARGUMENTS` directory
2. Examine and understand in depth the changes that were made in the last commit
3. Change back to the root directory
4. Merge in the worktree
5. Check for merge conflicts using `git status`, `git diff --name-only --diff-filter=U`, or `git ls-files -u`
6. Resolve the conflicts based on your knowledge of the changes and continue the merging process
