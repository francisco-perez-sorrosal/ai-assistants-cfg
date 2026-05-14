---
id: dec-draft-d012c144
title: Disposition-vocabulary step is Group A prerequisite; Groups B-H depend on shared reference
status: proposed
category: implementation
date: 2026-05-14
summary: The disposition-vocabulary file (dec-draft-1469273f) is created in Group A before any agent edits or command creation, because researcher.md, systems-architect.md, agents/verifier.md, and commands/resume-rework.md all cite the shared reference. Sequencing it first prevents dangling pointers at any commit boundary.
tags: [implementation, step-ordering, disposition-vocabulary, dependency]
made_by: agent
agent_type: implementation-planner
branch: worktree-verifier-rework-loop
pipeline_tier: standard
affected_files:
  - skills/software-planning/references/disposition-vocabulary.md
  - agents/researcher.md
  - agents/systems-architect.md
  - agents/verifier.md
  - commands/resume-rework.md
re_affirms: dec-draft-1469273f
---

## Context

The shared disposition vocabulary (`skills/software-planning/references/disposition-vocabulary.md`) is cited by at least four files: `agents/researcher.md`, `agents/systems-architect.md` (CIS redirect), `agents/verifier.md` (Phase 12.5), and `commands/resume-rework.md`. The implementation plan has 8 parallel execution groups (A through H). The question is: which group does the vocabulary file creation belong to?

Placing it in any group other than A means there is a window (during Groups B-H) where the pointer links exist in production code but the target file does not yet exist on disk — a broken-anchor state at commit boundaries.

## Decision

Vocabulary file creation (`skills/software-planning/references/disposition-vocabulary.md`) is Step 1 in Group A. The CIS redirects in `researcher.md` and `systems-architect.md` are Steps 1+2 in Group A (Steps 1 and 2 share the group; Step 2 is logically sequential after Step 1 but in the same group because both are prerequisites for all later groups). Groups B-H depend on Group A completing cleanly.

## Considered Options

**Option A: Create vocabulary in Group A (decided).**
- Pros: no broken pointers at any commit boundary; Group A is small (one file creation + two edits); integration checkpoint at Step 4 verifies pointer integrity before any code that consumes it exists.
- Cons: Group A is slightly serialized relative to Groups B-H; minor delay before the main work starts.

**Option B: Create vocabulary in Group C alongside verifier Phase 12.5.**
- Pros: vocabulary creation is co-located with its first consuming code (verifier Phase 12.5).
- Cons: `agents/researcher.md` and `agents/systems-architect.md` edits (which also need the file) are in Group A per the CIS redirect requirement; this creates a cross-group dependency that breaks the BDD parallel-group model.

**Option C: Create vocabulary in Group H (last group).**
- Rejected: all consuming files would have dangling pointers for the entire implementation phase.

## Consequences

- **Positive**: Every step that consumes or points to `disposition-vocabulary.md` is guaranteed to find the file on disk.
- **Positive**: Integration checkpoint at Step 4 confirms pointer integrity before Groups B-H begin.
- **Negative**: None material — Group A is small and fast.
