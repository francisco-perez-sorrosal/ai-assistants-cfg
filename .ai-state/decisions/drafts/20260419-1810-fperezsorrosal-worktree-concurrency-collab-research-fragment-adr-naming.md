---
id: dec-draft-5e4af711
title: Fragment-ADR Naming Scheme (Timestamp + User + Branch + Slug)
status: proposed
category: architectural
date: 2026-04-19
summary: ADRs created during a pipeline land as fragment files under `.ai-state/decisions/drafts/` with collision-safe timestamp+user+branch+slug filenames and `dec-draft-<hash>` ids; stable NNN assigned only at merge-to-main via finalize.
tags:
  - concurrency
  - adrs
  - fragment-naming
  - collaboration
made_by: agent
agent_type: systems-architect
pipeline_tier: full
affected_files:
  - "rules/swe/adr-conventions.md"
  - ".ai-state/decisions/drafts/"
  - "agents/systems-architect.md"
  - "agents/implementation-planner.md"
  - "agents/sentinel.md"
  - "scripts/reconcile_ai_state.py"
---

## Context

Praxion's current ADR naming scheme -- sequential `<NNN>-<slug>.md` with NNN assigned by scanning existing files -- is the root cause of every ADR-index-collision scenario in the codebase. Two worktrees can independently pick the same NNN; the post-merge reconciler currently detects and renumbers the later-alphabetical one, but cross-references from other ADRs (`supersedes: dec-042`, `re_affirms: dec-042`) and from `LEARNINGS.md` files pointing at the renumbered ADR become broken pointers. External research (scriv, reno, towncrier, branchnews) converged on a single answer: assign unstable identifiers at creation, stable identifiers at merge.

User decision frames this as Shape 2 of USER_DECISIONS.md -- "Fragment name at create, stable NNN at merge (towncrier / branchnews pattern)".

Multi-session-solo is the primary target, with documented extension to multi-user. That constrains the fragment-naming scheme to encode author identity from day one even when the author is always the same human today.

## Decision

ADRs created during a pipeline (by `systems-architect` or `implementation-planner` in any tier above Direct) land as fragment files in `.ai-state/decisions/drafts/` with filenames of the form:

```
<YYYYMMDD-HHMM>-<user>-<branch>-<slug>.md
```

Where:

- `YYYYMMDD-HHMM` is the UTC timestamp at creation (filename-safe, no colons).
- `<user>` is derived from `git config user.email` (username before `@`) or `git config user.name` when email is unset; falls back to `anon` when neither is available. Sanitized to `[a-z0-9-]`, capped at 40 chars.
- `<branch>` is `git rev-parse --abbrev-ref HEAD`, sanitized identically.
- `<slug>` is the kebab-case ADR title.

The frontmatter `id` field is `dec-draft-<8-char-hash>` where `<8-char-hash>` is the first 8 hex chars of the SHA-1 of the filename. This gives a stable, readable id inside the draft phase.

`status` is `proposed` on creation. Cross-references between drafts use `supersedes: dec-draft-<hash>`, `re_affirms: dec-draft-<hash>`, `superseded_by: dec-draft-<hash>` -- never a speculative `dec-NNN`.

Historical ADRs (001-055) keep their stable `NNN-slug.md` paths and `id: dec-NNN` -- no renumbering of merged history.

## Considered Options

### 1. Timestamp + user + branch + slug (chosen)

Pattern borrowed from scriv (`date+user+branch.<ext>`). Matches the full set of requirements:

- Collision-free across all three concurrency modes (solo, multi-session-solo, multi-user-team).
- Author identity encoded without an auxiliary system.
- Human-readable in PR diffs.
- Works pre-PR (no forge dependency).

### 2. PR-number-based (`<PR>.<slug>.md`)

Canonical towncrier fragment naming when a PR exists. Rejected: breaks for multi-session-solo before any PR exists, and couples the draft phase to the forge.

### 3. UUID (`<uuid>-<slug>.md`)

Collision-free, but unreadable in PR diffs -- reviewers cannot tell which ADR is which without opening each file. Rejected on reviewability grounds.

### 4. Content-hash (`<sha1-of-body>-<slug>.md`)

Collision-free and reproducible. Rejected: body edits change the filename, breaking cross-references during normal iteration.

## Consequences

**Positive:**

- Collision-free by construction: two concurrent worktrees cannot produce same filename (timestamp minute + branch differ).
- Author identity surfaces automatically -- forward-compatible with multi-user without schema change.
- Cross-reference dangling pointers removed at the source: drafts reference drafts by hash, finalize rewrites them atomically.
- Human-readable filenames preserved (scannable in PR reviews).
- No external dependency (towncrier or scriv avoided -- pattern reimplemented in stdlib Python).

**Negative:**

- Longer filenames than current `NNN-slug.md`.
- Filenames contain PII (email username prefix) -- acceptable for internal project state but flagged in the rule.
- Breaking change to existing ADR convention -- requires coordinated updates to rule, agents, sentinel checks, reconcile script.

**Risks:**

- Users with pathological branch names (spaces, unicode) rely on sanitizer correctness. Mitigation: sanitizer strips to `[a-z0-9-]`, caps length, tested.
- `user.email` unset case produces `anon` in filename. Mitigation: sentinel warning suggests setting git config.
