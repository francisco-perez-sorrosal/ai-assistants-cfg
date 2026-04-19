---
id: dec-draft-3c38eeb3
title: Auto-Memory Orphan Cleanup -- `/clean-auto-memory` opt-in command
status: proposed
category: implementation
date: 2026-04-19
summary: New `commands/clean-auto-memory.md` enumerates `~/.claude/projects/-<hash>-worktrees-*` directories, compares against `git worktree list`, surfaces orphans, and deletes only on user confirmation; never hook-driven.
tags:
  - concurrency
  - cleanup
  - auto-memory
  - commands
made_by: agent
agent_type: systems-architect
pipeline_tier: full
affected_files:
  - "commands/clean-auto-memory.md"
---

## Context

Claude Code's per-cwd auto-memory places transcripts and `MEMORY.md` under `~/.claude/projects/<repo-hash>/`. Worktrees get their own directories: `~/.claude/projects/-Users-<user>-<repo>--claude-worktrees-<slug>/`. When a worktree is removed, the auto-memory directory persists forever. Research confirmed 20+ orphan directories already exist on the current machine.

There is no Claude Code API for enumerating or cleaning these directories; there is no hook event for worktree removal. The cleanup must be user-initiated and user-gated.

## Decision

Create `commands/clean-auto-memory.md` -- opt-in slash command with `allowed-tools: [Bash, Read]`.

Command flow:

1. Enumerate `~/.claude/projects/` directories whose name ends with `-worktrees-*` (the canonical per-worktree pattern).
2. Run `git worktree list` in the current repo to get live worktrees.
3. Compute the set difference -- directories without a matching live worktree are orphans.
4. For each orphan, print path + size (`du -sh`).
5. Ask the user for a single batch confirmation ("[y/N]").
6. On confirmation, `rm -rf` each orphan directory.

No hook-driven auto-delete. No cleanup on session end.

Scope boundary: the command matches only `-worktrees-*` directory name patterns. The main-repo auto-memory directory (without `-worktrees-` suffix) is never touched regardless of user input.

A `--dry-run` flag prints orphans without asking for confirmation or deleting.

## Considered Options

### 1. Opt-in slash command (chosen)

User sees what is being deleted before any removal happens; no surprise data loss; orphans accumulate slowly enough that occasional manual runs suffice.

### 2. Stop-hook that deletes on session end

Rejected: hooks cannot prompt the user interactively; auto-delete risks removing auto-memory the user still references.

### 3. PostToolUse hook that cleans on worktree removal detection

Rejected: worktree removal is not directly observable from hooks; only indirectly via `git worktree list` delta. False-positive risk.

### 4. Separate script (not a slash command)

Rejected: slash command idiom matches existing `/clean-work` precedent; script placement under `scripts/` requires installation and PATH knowledge.

### 5. Do nothing

Rejected: 20+ orphans already accumulating; each session's worktree adds to the count; size is small but not zero, and the user expressed this as in-scope.

## Consequences

**Positive:**

- User controls every deletion.
- Matches existing `/clean-work` pattern for repository-scoped cleanup.
- Pattern-scoped to `-worktrees-*` so main-repo auto-memory is safe by construction.
- `--dry-run` supports inspection.

**Negative:**

- Orphans continue to accumulate until the user runs the command.
- User must remember to run it periodically.

**Risks:**

- User deletes auto-memory they still want. Mitigation: batch confirmation shows the list before deletion; `--dry-run` is the default inspection flow.
- Pattern match misses a worktree auto-memory with a non-standard path. Mitigation: the command is conservative -- misses are under-deletes, not over-deletes.
