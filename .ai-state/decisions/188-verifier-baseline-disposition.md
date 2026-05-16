---
id: dec-188
title: Verifier dispositions every failing test against a captured baseline
status: accepted
category: behavioral
date: 2026-05-15
summary: The verifier classifies each failing test as regression or pre-existing against a planner-captured baseline; an undisposed "pre-existing" label is a report-completeness FAIL.
tags: [verifier, pipeline, testing, tech-debt, quality-gate]
made_by: user
branch: test-baseline-disposition
pipeline_tier: direct
affected_files:
  - agents/verifier.md
  - agents/implementation-planner.md
  - rules/swe/agent-intermediate-documents.md
---

## Context

The verifier's Phase 10 instructed it to "classify each failure block against the current code state" — but with no record of which tests were already failing before the pipeline began, "pre-existing" was an unverifiable assertion. An orchestrator or verifier could close a task by labelling a failing test "pre-existing, out of scope" with no evidence and no tracking.

This conflates two distinct obligations. Declining to *fix* out-of-scope work is legitimate — it is what the Stay Surgical behavioral-contract clause requires. Declining to *report* a discovered failure is not — it violates the boy-scout principle ("leave what you touch better than you found it") and the Register Objection clause ("silent agreement is a contract violation"). The escape hatch worked precisely because "pre-existing" is often literally true, which made it a convincing shield.

The gap surfaced on 2026-05-15: a `/project-metrics` run with `--refresh-coverage` exposed five failing tests. They were dispositioned only because the user acted as the gate — an autonomous pipeline had no contract forcing it.

## Decision

The pipeline captures a test baseline before any code change, and the verifier dispositions every failing test against it.

1. The **implementation-planner** (Phase 6) runs the project's canonical test target once, on the still-unchanged codebase, and writes the failing test node IDs plus the base commit SHA to `.ai-work/<task-slug>/TEST_BASELINE.md`.
2. The **verifier** (Phase 10) classifies each failure in `TEST_RESULTS.md`:
   - **Regression** — failing now, not in the baseline. This pipeline caused it: emit `FAIL`, route to rework.
   - **Pre-existing** — failing now and in the baseline. Disposition it: fix it in scope when the fix is trivial and adjacent, otherwise append a `td-NNN` row to `.ai-state/TECH_DEBT_LEDGER.md` and emit a `WARN` citing the row.
3. An **undisposed** "pre-existing" label — neither fixed nor ledgered — is itself a report-completeness `FAIL`. "Pre-existing" alone is not a closeable disposition.
4. When `TEST_BASELINE.md` is absent (standalone verification, or capture skipped), every current failure is treated conservatively as pre-existing and must still be dispositioned.
5. `TEST_BASELINE.md` is registered as a `.ai-work/` ephemeral artifact.

The asymmetry is deliberate: a regression `FAIL`s and blocks; a pre-existing failure only `WARN`s, but the `WARN` carries a mandatory ledger row. This matches Phase 10's existing severity grammar (a missing `TEST_RESULTS.md` is already `WARN`-not-`FAIL`).

## Considered Options

### Planner-captured baseline (chosen)

The implementation-planner captures the baseline at pipeline setup; the verifier does cheap set-membership at verification time.

- **Pros**: capture happens once, on unchanged code, at a natural pipeline-setup point; the verifier never manipulates git state; degrades gracefully when the baseline is absent; the planner is Standard/Full-only, exactly matching where the verifier and rework machinery apply.
- **Cons**: one extra full test run per Standard/Full pipeline.

### Verifier re-runs failing tests against the base commit

The verifier checks out or stashes to the base commit and re-runs only the failing tests to decide regression-vs-pre-existing.

- **Pros**: no new artifact, no cross-agent contract, no planner change.
- **Cons**: the verifier must manipulate git working state, which is fragile and outside its read-mostly role; re-running at verification time is later and riskier than capturing up front.

### No baseline; tighten the disposition prose only

Leave Phase 10 baseline-free and merely instruct the verifier to "track pre-existing failures."

- **Pros**: smallest possible change.
- **Cons**: does not fix the root cause — "pre-existing" stays unfalsifiable, so the instruction is unenforceable and the escape hatch survives.

## Consequences

**Positive.** "Pre-existing" becomes a checkable, tracked claim rather than a prose escape hatch. Every failing test at verification time is now either fixed, ledgered, or a blocking `FAIL` — there is no silent-close path. The third `FAIL` case (undisposed pre-existing) gives the contract structural teeth: the verifier `FAIL`s its own report for being incomplete, so the qualifying sentence alone no longer closes a task.

**Negative.** One extra full test run per Standard/Full pipeline at planner setup. The contract is unverified until exercised by a real pipeline. ML-training pipelines, whose "suite" is a training run, need the metric-threshold model instead of a test-node-ID baseline — noted inline in the planner change as a carve-out, but not yet fully specified.
