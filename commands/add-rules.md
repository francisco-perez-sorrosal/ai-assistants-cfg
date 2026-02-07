---
description: Add rules from personal library to the current project
argument-hint: [rule-names... | all]
allowed-tools: [Bash(mkdir:*), Bash(cp:*), Bash(ls:*), Bash(find:*), Read, Glob, Grep]
---

Add rules to the current project's `.claude/rules/` directory by copying them from the personal rules library (`~/.claude/rules/`).

## Arguments

- `$ARGUMENTS` — Space-separated rule names (filename stem without `.md`) or `all`
- Examples: `/add-rules coding-style git-commit-hygiene`, `/add-rules all`

## Process

1. Verify `~/.claude/rules/` exists and contains rule files
2. Scan `~/.claude/rules/` recursively for `.md` files — build a map of filename stem → relative path (e.g., `coding-style` → `swe/coding-style.md`)
3. If no arguments provided, list available rules (stem and relative path) and ask the user which ones to add
4. If `$ARGUMENTS` is `all`, select every available rule. Otherwise, match each argument against the filename stem map
5. For each selected rule:
   a. If the rule already exists at the target path under `.claude/rules/`, skip it and report "already exists"
   b. Create the target subdirectory under `.claude/rules/` if needed (preserve source directory structure)
   c. Copy the rule file to the target location
6. Report summary: rules added, rules skipped, rules not found

## Important

- **Copy, do not symlink** — project rules must be independent, customizable, and committable to git
- **Preserve subdirectory structure** — `swe/coding-style.md` → `.claude/rules/swe/coding-style.md`
- **Never overwrite** — if a rule already exists in the project, skip it and inform the user
- **Ignore README.md files** — only copy rule content files, not directory documentation
