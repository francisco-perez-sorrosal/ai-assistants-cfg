---
description: Onboard the current project to work with the ai-assistants plugin ecosystem
allowed-tools: [Bash(git:*), Bash(grep:*), Bash(claude:*), Read, Write, Edit, Glob, Grep, AskUserQuestion]
---

Onboard the current project directory to work cleanly with the ai-assistants plugin (i-am). Run checks and apply fixes for `.gitignore` hygiene, plugin installation, and project-level configuration.

## Pre-flight

1. Confirm the working directory is a git repository (`git rev-parse --git-dir`). If not, stop: "This command must be run inside a git repository."
2. Detect the project root (`git rev-parse --show-toplevel`) and work relative to it for all checks

## Checks

Run all checks, collect results, then present a summary before making changes. Group into **needs action** and **looks good**.

### 1. `.gitignore` hygiene

Check that the project's root `.gitignore` contains these entries:

- `.ai-work/` -- ephemeral pipeline intermediates (must not be committed)

If `.gitignore` does not exist, create it with the required entries. If it exists but entries are missing, append them under an `# AI assistants` comment block. Do not duplicate entries already present.

### 2. `.ai-state/` not excluded

`.ai-state/` is persistent project intelligence and SHOULD be committed. Check whether `.gitignore` contains `.ai-state/` or `.ai-state`. If found, flag it as a warning: ".ai-state/ is excluded from git but should be committed -- it contains persistent project intelligence (idea ledgers, sentinel reports)." Ask the user whether to remove the exclusion entry.

### 3. Plugin installation

Check whether the i-am plugin is installed and accessible:

- Run `claude plugin list 2>/dev/null | grep -i "i-am" || echo "NOT_FOUND"`
- If not found, warn: "The i-am plugin is not installed. Run install.sh from the ai-assistants repo to install it."
- If installed, inform the user about it and ask him if he wants to try to update it with `claude plugin install --scope user i-am`

### 4. Project CLAUDE.md

Check whether a `CLAUDE.md` file exists at the project root.

- If missing, suggest: "No project-level CLAUDE.md found. Run `claude init` to generate one from the codebase." Do not create it directly -- `claude init` analyzes the project and produces better results.
- After `claude init` completes (or if `CLAUDE.md` already exists), append this line if not already present:

```
Prefer delegating to specialized agents (researcher, context-engineer, implementer, etc.) over doing multi-step work directly.
```

### 5. Existing `.ai-work/` leftovers

Check if `.ai-work/` exists with content from a previous session. If found, note: ".ai-work/ contains leftover pipeline files. Run /clean-work to clean up when ready."

## Apply Changes

After presenting the summary:

1. Ask the user to confirm before making any changes
2. Apply `.gitignore` fixes (if needed)
3. Apply `.ai-state/` exclusion removal (if user approved)
4. Create `CLAUDE.md` (if user approved)
5. Stage and commit only the files this command changed, with message: `chore: Onboard project for ai-assistants plugin`
6. Print final summary of what was done
