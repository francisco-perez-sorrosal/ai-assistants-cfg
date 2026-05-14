---
id: dec-draft-d70b274f
title: REWORK_MANIFEST.md is ephemeral alongside VERIFICATION_REPORT.md; parent cleanup deferred; VERIFICATION_REPORT.md snapshotted into each rework worktree
status: proposed
category: architectural
date: 2026-05-14
summary: REWORK_MANIFEST.md lives in .ai-work/<parent-task-slug>/ (ephemeral, same lifecycle as VERIFICATION_REPORT.md). Parent pipeline cleanup is gated on rework-worktree completion. At worktree creation, the parent's VERIFICATION_REPORT.md is snapshotted into the rework worktree's .ai-work/<rework-slug>/ for provenance survival.
tags: [manifest, lifecycle, ephemeral, worktree-cleanup, provenance]
made_by: agent
agent_type: systems-architect
branch: worktree-verifier-rework-loop
pipeline_tier: standard
affected_files:
  - rules/swe/agent-intermediate-documents.md
  - rules/swe/swe-agent-coordination-protocol.md
  - agents/verifier.md
---

## Context

Three lifecycle questions arise for the rework loop:

1. Does `REWORK_MANIFEST.md` belong in `.ai-work/<parent-slug>/` (ephemeral, deleted with the pipeline) or in `.ai-state/` (persistent, committed to git as an audit trail)?
2. When is the parent pipeline's `.ai-work/<parent-slug>/` deleted? Immediately after the verifier completes? After the user invokes cleanup? After all reworks merge?
3. The rework worktree's `VERIFIER_FINDINGS.md` references the parent's `VERIFICATION_REPORT.md` in its `## Provenance` section. If the parent's `.ai-work/` is gone, that reference dangles. Snapshot the report at creation, or defer cleanup, or both?

**Activation:** yes (cross-cutting lifecycle decision; cleanup behavior affects user workflow). Lenses applied: Simplicity (no new permanent surface), Future-proof, Correctness (no lost provenance), Idempotency.

## Decision

### Lifecycle of `REWORK_MANIFEST.md`: ephemeral

`REWORK_MANIFEST.md` lives at `.ai-work/<parent-task-slug>/REWORK_MANIFEST.md` alongside `VERIFICATION_REPORT.md`. Same lifecycle, same tier. It is registered in `rules/swe/agent-intermediate-documents.md` § Ephemeral tier (one new table row).

### Parent cleanup: gated on rework completion

When the user invokes pipeline cleanup on the parent task slug (`rm -rf .ai-work/<parent-slug>/` or via a future `/cleanup-pipeline` command), the main agent:

1. Reads `REWORK_MANIFEST.md` (if present) and extracts each row's `worktree_name`.
2. Checks `.claude/worktrees/<name>/` for each row — exists means the rework is in-flight or unmerged.
3. Lists the open reworks to the user and asks explicit confirmation: "Cleanup will remove REWORK_MANIFEST.md and VERIFICATION_REPORT.md. The following rework worktrees are still open: [...]. Proceed?"
4. On confirmation, deletes; on decline, exits.

The cleanup behavior is codified in `rules/swe/swe-agent-coordination-protocol.md` as a one-bullet rule in the Pipeline Rules table.

### Snapshot at creation

At rework-worktree creation time, the main agent copies `VERIFICATION_REPORT.md` from the parent's `.ai-work/<parent-slug>/` into the new worktree's `.ai-work/<rework-slug>/VERIFICATION_REPORT.snapshot.md`. The `VERIFIER_FINDINGS.md` `## Provenance` section's report-link uses the snapshot path (relative to the rework worktree).

This decouples the rework worktree from the parent's `.ai-work/` lifetime: even if the user cleans up the parent against guidance (or a bug forces premature cleanup), the rework worktree still has its source provenance.

## Considered Options

### Manifest lifecycle: Option A — Ephemeral (chosen)

Pros: matches `VERIFICATION_REPORT.md` lifecycle (manifest is derivative); zero git-history pollution; one ephemeral-tier row addition to the artifact registry.

Cons: no long-term audit trail of which clusters were addressed how. Mitigation: the persistent record lives in `TECH_DEBT_LEDGER.md` (active and resolved rows); `resolved-by` carries the merge commit SHA; git log of the rework worktree branch reconstructs the journey.

**Chosen.**

### Manifest lifecycle: Option B — Persistent (.ai-state/rework_manifests/REWORK_MANIFEST_<timestamp>.md)

Pros: long-term audit trail; queryable history of every rework decision.

Cons: new permanent state surface; git-history pollution; another `.ai-state/` directory to maintain (sentinel checks, schema discipline); duplicates what `TECH_DEBT_LEDGER.md` already records.

Rejected.

### Manifest lifecycle: Option C — Hybrid: ephemeral file + persistent append-only log at .ai-state/rework_log.md

Pros: lightweight audit trail without per-manifest file accumulation.

Cons: introduces a new persistent artifact for marginal value; the same information is already in `TECH_DEBT_LEDGER.md` rows and their `resolved-by` fields.

Deferred — if audit demand grows, this is the migration path (one append-only file is cheap; the per-manifest persistent file is not).

### Parent cleanup: Option α — Unconditional cleanup after verifier completes

Pros: simplest; no gating logic.

Cons: deletes the manifest before reworks complete; the user loses the ability to re-read the source report once cleanup runs.

Rejected.

### Parent cleanup: Option β — Defer cleanup until all reworks merge (chosen)

Pros: manifest's lifetime matches the reworks it spawned; user has the source report available throughout the rework cycle.

Cons: stale `.ai-work/<parent-slug>/` accumulates until the user explicitly cleans up. Mitigation: the open-rework count is surfaced when cleanup is invoked; the user is informed and decides.

**Chosen.**

### Provenance: Option Ⅰ — Snapshot VERIFICATION_REPORT.md at rework creation (chosen)

Pros: rework worktree is self-sufficient even if the parent is cleaned up prematurely or by a buggy script.

Cons: ~10–100KB extra disk per rework worktree. Negligible.

**Chosen.**

### Provenance: Option Ⅱ — Reference parent path only (no snapshot)

Pros: zero extra disk.

Cons: dangles if parent is cleaned up; couples rework worktree's correctness to parent's lifetime.

Rejected.

## Consequences

**Positive:**

- The rework worktree is self-contained: it has the findings, the provenance, and the snapshotted source report.
- Cleanup is informed: the user sees the open-rework count and decides.
- The `.ai-state/` surface is unchanged — no new persistent directory.
- Git history reflects rework outcomes via the merge commits + `td-NNN` resolutions; the persistent audit trail is implicit and adequate.

**Negative:**

- Parent `.ai-work/` directories accumulate until the user cleans up. Disk usage is small (typically <1MB per pipeline); not a concern.
- Snapshot copies disk per rework worktree. Bounded and small.

**Mitigation:**

- A future `/cleanup-stale-pipelines` command could automate the open-rework check; this is a separate, additive feature.
- If audit demand grows, Option C (append-only `.ai-state/rework_log.md`) is a cheap retrofit.
