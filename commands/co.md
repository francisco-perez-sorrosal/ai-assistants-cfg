---
description: Create a commit for staged (or all) changes
argument-hint: [message]
allowed-tools: [Bash(git:*), Read, Grep]
---

Create a commit for the current staged changes (or all changes if nothing is staged).

## Process

1. Run `git status` and `git diff --staged` (or `git diff` if nothing staged)
2. Analyze the changes to understand their purpose and scope
3. Stage files if needed (prefer specific files over `git add -A`)
4. Craft the commit message following our commit conventions
5. Create the commit
6. If `.ai-work/` exists, ask the user whether to clean it up (`rm -rf .ai-work/`). Before deleting, check for `LEARNINGS.md` and remind the user to merge any valuable content into permanent locations first
