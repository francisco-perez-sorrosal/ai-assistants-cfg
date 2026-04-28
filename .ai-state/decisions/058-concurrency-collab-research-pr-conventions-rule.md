---
id: dec-058
title: PR-Conventions Rule -- path-scoped, no always-loaded budget impact
status: proposed
category: behavioral
date: 2026-04-19
summary: A new `rules/swe/vcs/pr-conventions.md` rule covers branch naming, `.ai-state/` safety at PR time, merge policy (reject squash on `.ai-state/` PRs), review expectations, and forward path for multi-user mode; path-scoped via YAML frontmatter so zero always-loaded budget consumption.
tags:
  - concurrency
  - collaboration
  - pr
  - conventions
  - rules
made_by: agent
agent_type: systems-architect
pipeline_tier: full
affected_files:
  - "rules/swe/vcs/pr-conventions.md"
  - "rules/swe/vcs/git-conventions.md"
  - "commands/merge-worktree.md"
  - "commands/release.md"
---

## Context

Existing `rules/swe/vcs/git-conventions.md` covers commit scope, staging, secrets, subject/body format, and "no AI authorship" -- but says nothing about PR workflow, merge policy, or multi-user collaboration. The only mention of PRs in the rule set is a one-line warning about GitHub squash-merge breaking `.ai-state/` reconciliation (in `skills/software-planning/references/agent-pipeline-details.md`).

User decision is explicit: "PR-workflow rule ... covering branch naming, squash-merge guard, `.ai-state/` safety at PR time, review expectations." The question is where to put it and how to avoid consuming the 25,000-token always-loaded budget.

Precedent: `rules/swe/coding-style.md` is path-scoped (applies when editing code files). `rules/swe/staleness-policy.md` is path-scoped (applies when editing skill files). The same pattern applies here: PR conventions are relevant when editing PR-adjacent surfaces (`.github/`, PR-related commands, release command) and nowhere else.

## Decision

Create `rules/swe/vcs/pr-conventions.md` with YAML frontmatter path-scoping:

```yaml
---
paths:
  - ".github/**/*.md"
  - "commands/*pr*.md"
  - "commands/*merge*.md"
  - "commands/release.md"
  - "rules/swe/vcs/git-conventions.md"
---
```

Zero tokens added to the always-loaded budget. The rule loads only when editing PR-relevant surfaces.

Content sections (the planner/implementer fleshes out text during implementation):

1. **Branch naming.** Short-lived, topic-based (`feat/<slug>`, `fix/<slug>`, `docs/<slug>`); author-prefixed when multi-user (`<user>/<topic>`). Matches existing `commands/create-worktree.md` convention.
2. **`.ai-state/` safety contract at PR time.**
   - Before opening a PR: run `python scripts/finalize_adrs.py --dry-run` locally; confirm drafts will finalize correctly at merge.
   - PR description must explicitly mention when `.ai-state/` is touched so reviewers know semantic merge applies.
3. **Merge policy.**
   - Default: "Create a merge commit" -- preserves merge drivers and post-merge hook execution.
   - Reject squash merges on PRs touching `.ai-state/`. Enforced as post-hoc warning (see dec-059); the rule calls it out explicitly.
   - Rebase-and-merge is acceptable if reconciliation runs locally first.
4. **Review expectations for `.ai-state/`-touching PRs.**
   - Reviewers verify ADR drafts have required frontmatter per dec-056.
   - Reviewers do NOT review `DECISIONS_INDEX.md` changes -- regenerated post-merge, not authored.
5. **Forward path for multi-user mode.** Author identity already encoded in fragment filenames (dec-056); `finalize_adrs.py --author <email>` per-author filtering is a 10-line extension.

`rules/swe/vcs/git-conventions.md` -- add one line: "See also: [`pr-conventions.md`](pr-conventions.md) for PR-specific workflow." No duplication. <!-- validate-references:ignore -->
<!-- The bracketed link above is template content showing what to insert into git-conventions.md (where the relative path resolves correctly); it is not a navigable link from this ADR. -->

## Considered Options

### 1. New path-scoped rule `rules/swe/vcs/pr-conventions.md` (chosen)

Lives alongside `git-conventions.md`, follows existing path-scoping precedent from `coding-style.md` and `staleness-policy.md`. Zero always-loaded budget impact.

### 2. Extend `rules/swe/vcs/git-conventions.md` with PR sections

Rejected: would make `git-conventions.md` always-loaded much larger; commit conventions and PR conventions have non-overlapping activation scopes.

### 3. New unconditional (always-loaded) PR rule

Rejected: cost is too high for a rule that fires only when users are actively editing PR surfaces. Violates the "every always-loaded token must earn its attention share in >30% of sessions" principle.

### 4. Fold the rule content into `commands/merge-worktree.md` and `commands/release.md`

Rejected: cross-command duplication; no single authoritative source for PR conventions.

## Consequences

**Positive:**

- Zero always-loaded budget cost.
- Single source of truth for PR conventions, referenced by commit-conventions and by PR-related commands.
- Forward-compatible with multi-user: extension points documented.
- Path-scoped activation matches existing `coding-style.md` and `staleness-policy.md` precedents.

**Negative:**

- Users editing files OUTSIDE the scoped paths will not see the rule -- if a user drafts a PR description in an unscoped context, they lack the convention. Mitigation: the PR template (part of the rule's `.github/` scope) surfaces the key bullets inline.

**Risks:**

- Path-scope pattern misses a relevant surface (e.g., `CHANGELOG.md`). Mitigation: the rule has explicit "See also" cross-links from git-conventions; users are not solely dependent on scope match.
