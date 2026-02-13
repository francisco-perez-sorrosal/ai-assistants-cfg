---
description: Clean the .ai-work/ directory after pipeline completion
allowed-tools: [Bash(rm:*), Bash(ls:*), Bash(cat:*), Read, AskUserQuestion]
---

Remove the `.ai-work/` directory containing ephemeral pipeline intermediates.

## Process

1. Check if `.ai-work/` exists. If not, report that there is nothing to clean and stop
2. List the contents of `.ai-work/` so the user can see what will be removed
3. If `.ai-work/LEARNINGS.md` exists, display its contents and warn: "LEARNINGS.md exists and may contain insights worth preserving. Merge valuable content into permanent locations (e.g., project CLAUDE.md, rules, skills, or .ai-state/) before deleting." Ask the user whether to proceed or abort
4. If the user confirms (or LEARNINGS.md does not exist), run `rm -rf .ai-work/`
5. Confirm deletion
