---
id: dec-119
title: Extend verifier with eval-aware mode rather than introducing a peer ml-verifier
status: proposed
category: architectural
date: 2026-05-03
summary: Verifier gains an eval-aware Phase 3 sub-branch that reads TRAINING_RESULTS.md and evaluates metric thresholds instead of branching into a separate agent.
tags: [ml-training, verifier, agent-pipeline, archetype-extension]
made_by: agent
agent_type: systems-architect
pipeline_tier: standard
affected_files:
  - agents/verifier.md
  - skills/llm-training-eval/SKILL.md
  - rules/ml/eval-driven-verification.md
affected_reqs: []
---

# ADR — Verifier extension for ML eval-aware verification

## Context

ML pre-training projects produce continuous, stochastic acceptance signals: `val_bpb < 1.75`, `perplexity < 12.4`, `val_loss does not regress against baseline`. These cannot be evaluated by code inspection or by running a unit-test suite — they require either (a) a completed training run whose metrics were captured, or (b) reading an external tracker (MLflow / W&B). Praxion's existing `verifier` agent has 12 phases, of which Phase 3 (Acceptance Criteria Validation) is the only phase that strains: the other 11 phases (convention compliance, behavioral contract, deployment validation, architecture validation, security review, test coverage, context artifact completeness, etc.) are domain-agnostic and apply to ML projects unchanged.

The `RESEARCH_FINDINGS.md` "Theme 4 — Verifier strain is the load-bearing structural break" identifies this as the only "extend a structurally critical agent" decision in v1. Two options were named:

1. Extend `verifier` with eval-aware mode (recommended)
2. Introduce peer `ml-verifier`

The decision shapes how `TRAINING_RESULTS.md` is consumed, who owns its schema, and how the verifier pipeline branches.

## Decision

**Extend the existing `verifier` agent.** Phase 3 gains an eval-aware sub-branch triggered when the `SYSTEMS_PLAN.md` acceptance criteria contain metric thresholds (detected by syntax — e.g., a numeric comparator on a named metric). When triggered, Phase 3 reads `.ai-work/<task-slug>/TRAINING_RESULTS.md` and evaluates each metric criterion against the artifact's recorded values, classifying as PASS / FAIL / WARN with a tolerance band declared in the plan.

The `TRAINING_RESULTS.md` schema is owned by the `llm-training-eval` skill (see ADR `dec-116`). Verifier reads what the skill defines; verifier remains declarative.

## Considered Options

### Option 1 — Extend verifier (chosen)

**Pros:**
- Single review surface; behavioral-contract, convention, deployment, and architecture phases continue to apply to ML projects with no changes
- No coordination logic to decide which verifier handles which acceptance criteria
- Smaller blast radius (~30 lines added to one phase of one agent file)
- Existing pipeline cycle (verifier → user → planner → re-verify) works for ML the same as SWE
- Verifier's tech-debt ledger writes (Phase 5/5.5) continue to fire on ML projects' surrounding code without modification

**Cons:**
- Verifier agent file grows in surface area
- A future ML-specific code-quality concern that is structurally distinct from SWE code quality may push verifier toward unwanted complexity (deferred risk)

### Option 2 — Peer `ml-verifier`

**Pros:**
- Clean separation of concerns
- ML-specific phases can evolve independently
- Dedicated agent could specialize in metric tolerance bands, statistical significance tests, baseline comparison

**Cons:**
- Doubles the verification surface
- Requires a coordination agent or rule to decide which verifier runs (or both, with merge logic)
- Behavioral-contract and convention-compliance phases would have to be duplicated or factored out — neither is cheap
- New agent prompt to write, version, and maintain
- Risk of divergence between the two verifiers' interpretations of overlapping phases

## Consequences

**Positive:**
- The `verifier` extension is the smaller, more surgical change
- The pipeline's existing self-healing loop (verifier finds issue → planner creates corrective step → implementer fixes → re-verify) works unchanged
- The new `eval-driven-verification` rule defines the conventions; verifier reads them
- Future ML evaluation features (statistical significance, baseline comparison, multi-metric optimization) extend the same Phase 3 sub-branch

**Negative:**
- Verifier's Phase 3 grows to ~40-50 lines including the eval branch — close to but under the 50-line function ceiling. If it grows further, refactor into a `evaluate_metric_threshold` helper.
- Verifier is now both a SWE and an ML reviewer — its frontmatter description, model tier, and prompt budget were sized for SWE; revisit if ML reviews push budget past comfort

**Neutral:**
- Coordination with `llm-training-eval` skill: when the skill's `TRAINING_RESULTS.md` schema changes, verifier must be updated. Mitigated by the skill being the single source of truth and by sentinel staleness checks.
