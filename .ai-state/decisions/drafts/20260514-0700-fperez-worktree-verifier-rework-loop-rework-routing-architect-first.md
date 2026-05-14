---
id: dec-draft-b3b1abda
title: All rework worktrees route through systems-architect first
status: proposed
category: architectural
date: 2026-05-14
summary: Every REWORK_MANIFEST.md row dispatches systems-architect first (regardless of class); implementation-class reworks then chain to implementation-planner via the existing self-healing-loop contract — preserves planner's input-shape invariant and avoids any internal planner change.
tags: [verifier, rework, routing, architect, planner, pipeline-contract]
made_by: agent
agent_type: systems-architect
branch: worktree-verifier-rework-loop
pipeline_tier: standard
affected_files:
  - agents/verifier.md
  - commands/resume-rework.md
re_affirms: dec-draft-9fabb0e1
---

## Context

When the verifier emits a `REWORK_MANIFEST.md`, each row carries a `class` field (`architecture` or `implementation`). The natural first instinct is class-keyed routing: architecture-class rows go to `systems-architect`, implementation-class rows go to `implementation-planner`. The user's original framing for this feature also preferred this split.

The complication is that `implementation-planner` Phase 1 explicitly requires `SYSTEMS_PLAN.md` as primary input: "If `SYSTEMS_PLAN.md` does not exist or lacks architecture sections, recommend invoking the systems-architect agent first." (agents/implementation-planner.md). A rework worktree carrying only `VERIFIER_FINDINGS.md` violates this invariant. Two ways to resolve:

- **Option A (split-routing)** — Patch the planner to accept `VERIFIER_FINDINGS.md` as primary input when `SYSTEMS_PLAN.md` is absent. Adds a rework-specific branch in the planner. Violates the load-bearing hypothesis of `dec-draft-9fabb0e1` (no internal agent change beyond one sentence).
- **Option B (architect-always-first)** — Spawn the architect first on every rework; the architect produces a small `SYSTEMS_PLAN.md`; the planner then runs as usual (for implementation-class clusters) reading the architect's output. No planner change beyond one Phase 1 sentence — and that sentence is only effective via the architect's output, which is the file the planner already expects.

The decision drives the manifest's `target_agent` field semantics, the `/resume-rework` dispatch logic, and the load-bearing hypothesis the interface-designer's existing draft assumes.

**Activation:** yes (cross-cutting routing decision, multi-axis trade-off with downstream blast radius, behavioral-contract surface). Lenses applied: Simplicity, Testability, Hard-to-misuse, Behavioral-contract (Surface Assumptions, Register Objection).

## Decision

All rework worktrees route through `systems-architect` first, regardless of the manifest row's `class` value. The architect runs its standard Phase 1–10 on the `VERIFIER_FINDINGS.md` file and produces a `SYSTEMS_PLAN.md`. For implementation-class clusters, the orchestrator then spawns `implementation-planner` (which reads the architect's `SYSTEMS_PLAN.md` per its standard Phase 1 contract) and the rest of the pipeline (implementer + test-engineer + verifier) flows as usual.

The manifest's `target_agent` field is therefore informational: it tells the user which final agent will own the rework. The first hop is always the architect.

Concretely:

- `/resume-rework` always spawns `systems-architect` first.
- The architect's tier-selection step (per `swe-agent-coordination-protocol.md` § Process Calibration) governs whether the resulting plan is Direct, Lightweight, Standard, or Full.
- A Direct- or Lightweight-tier architect output is acceptable — for a one-line rename, the architect produces a one-paragraph plan; the planner sees a small plan and decomposes it into a one-step plan.

## Considered Options

### Option A — Split routing: architecture→architect, implementation→planner

Pros: shorter critical path for trivial implementation-reworks (planner runs immediately without architect overhead); matches the user's original framing.

Cons: requires patching `agents/implementation-planner.md` Phase 1 to accept `VERIFIER_FINDINGS.md` as primary input when `SYSTEMS_PLAN.md` is absent (an internal-logic branch, not a one-sentence addition); breaks the load-bearing hypothesis of `dec-draft-9fabb0e1`; introduces a "verifier classified wrong → planner gets wrong-shape file" failure mode; the verifier's classification becomes load-bearing rather than advisory.

Rejected.

### Option B — Architect-always-first (chosen)

Pros: zero internal change to the planner's input-shape invariant; uniform dispatcher logic (`/resume-rework` always spawns the same agent); the manifest's `class` field stays advisory; the architect's Phase 1 tier-selection re-evaluates the verifier's `Suggested Tier`, exercising the existing calibration discipline; the load-bearing hypothesis (no internal agent changes beyond one sentence each) holds.

Cons: each implementation-class rework absorbs the wall-clock cost of one architect Phase-1-through-Phase-7 pass for what may be a trivial fix.

**Chosen.** The simplicity, testability, and hard-to-misuse wins outweigh the latency cost. The architect on a focused 7-section findings file collapses Phase 5/6/7 quickly; total cost for a Direct-tier rework is small.

### Option C — Defer routing decision; let the user pick at /resume-rework time

Pros: maximum flexibility; the user can override per worktree.

Cons: every `/resume-rework` invocation becomes interactive; defeats the "fresh session → zero-typing dispatch" flow that motivates the feature; introduces inconsistency across rework worktrees of the same kind.

Rejected.

## Consequences

**Positive:**

- `agents/implementation-planner.md` requires only the one-sentence addition documented in `dec-draft-9fabb0e1` — and that addition is effectively only exercised when an architect step is somehow skipped (e.g., the user runs `/resume-rework` and the architect step fails before producing a plan; the planner's existing fallback message tells the user to re-invoke the architect first).
- The verifier's smell classification is downgraded from load-bearing to advisory — failure modes from mis-classification are contained.
- The manifest's `class` field becomes user-facing context, not orchestrator-routing logic — easier to reason about.
- The re-run gate (Decision 8 in `SYSTEMS_PLAN.md`) is simpler: after rework merges to main, the user re-invokes the verifier on the parent task slug; the verifier sees the corrective work and updates `td-NNN` rows.

**Negative:**

- A trivial implementation-smell ("typo in a docstring") still costs one architect Phase 1 pass. For a busy pipeline with many small smells, latency accumulates.
- The architect's authority surface expands slightly: it now sees rework intake as part of its normal task surface, not as a separate flow.

**Mitigation:**

- The decision is reversible. Re-litigating to Option A requires patching `agents/implementation-planner.md` Phase 1 (which is the cost we are deferring), not unwinding the rework loop infrastructure.
- A future evolution could short-circuit the architect for `recommended_tier: direct` rework rows; this would be an additive optimization atop Option B, not a contract change.

## Prior Decision

This ADR re-affirms `dec-draft-9fabb0e1` (verifier-findings schema as self-contained problem statement). That draft did not specify routing; this draft fills that gap and confirms the load-bearing hypothesis remains valid: no internal change to receiving agents beyond one Phase 1 sentence each.
