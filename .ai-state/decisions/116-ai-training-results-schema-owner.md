---
id: dec-116
title: TRAINING_RESULTS.md schema is owned by llm-training-eval skill; verifier reads it; /run-experiment writes it
status: proposed
category: architectural
date: 2026-05-03
summary: The schema for TRAINING_RESULTS.md is defined and versioned by the llm-training-eval skill. /run-experiment (and any future training dispatcher) writes the artifact at run completion; verifier's eval-aware Phase 3 reads it. The artifact lives ephemerally in .ai-work/<slug>/ and may be archived to .ai-state/training_runs/<run-tag>.md when the run is "kept" per the autoresearch experiment loop.
tags: [ml-training, training-results, schema-ownership, verifier, llm-training-eval, archetype-extension]
made_by: agent
agent_type: systems-architect
pipeline_tier: standard
affected_files:
  - skills/llm-training-eval/SKILL.md
  - agents/verifier.md
  - commands/run-experiment.md
  - rules/ml/eval-driven-verification.md
affected_reqs: []
---

# ADR — `TRAINING_RESULTS.md` schema ownership

## Context

The eval-aware verifier mode (dec-119) reads `TRAINING_RESULTS.md` to evaluate metric thresholds. Three ownership questions follow:

1. **Schema location.** Where does the schema definition live?
2. **Writer.** Who writes the artifact?
3. **Lifecycle.** Is it ephemeral (`.ai-work/<slug>/`) or persistent (`.ai-state/training_runs/`)?

The autoresearch reference architecture has `results.tsv` (untracked, project-local) as the experiment log. Praxion's analog needs to integrate cleanly with the verifier pipeline while not displacing project-side conventions.

## Decision

**Schema ownership: `llm-training-eval` skill.** The skill's body declares the canonical YAML / Markdown schema (one section). The verifier reads this section to know what fields to expect. The `/run-experiment` command writes the artifact at run completion using the same schema. Updates to the schema flow through skill versioning (and trigger a sentinel staleness check on dependent agents).

**Writer: `/run-experiment` command** (synchronously, at the end of dispatch). For the autoresearch case where the experiment loop runs autonomously inside the project, the loop writes `TRAINING_RESULTS.md` directly using the schema; `/run-experiment` is the Praxion-facing wrapper that ensures the artifact is produced regardless of who triggered it.

**Lifecycle: dual.** Ephemeral primary location is `.ai-work/<task-slug>/TRAINING_RESULTS.md` — read by verifier in the current pipeline and deleted with `.ai-work/` cleanup. When the run is "kept" per the autoresearch git-commit semantics (val_bpb improved → branch advances), an archival copy is written to `.ai-state/training_runs/<run-tag>.md` for cross-pipeline reproducibility audit. When the run is rejected, only the ephemeral copy exists.

**Canonical schema** (defined in `skills/llm-training-eval/SKILL.md`):

```yaml
# TRAINING_RESULTS.md (front-matter is YAML, body is Markdown)
---
schema_version: "1.0"
run_tag: <string>
git_commit: <sha>
descriptor: <path>          # path to training_job_descriptor used
backend: local | skypilot | runpod-direct | <other>
started_at: <ISO 8601>
ended_at: <ISO 8601>
wall_clock_seconds: <float>
gpu_hours: <float>
metrics:
  val_bpb: <float>          # primary metric; lower=better; required for pre-training
  val_loss: <float>          # optional secondary
  perplexity: <float>        # optional secondary
  custom_metrics: { <k>: <v> }
status: completed | failed | crashed | timeout | cancelled
crash_reason: <string>      # populated only when status = crashed/failed
artifacts:
  checkpoint_path: <path>   # optional; URI or local path
  log_path: <path>           # path to run.log
acceptance:
  evaluated_against: <list[string]>  # criterion names from SYSTEMS_PLAN.md
  outcome: pass | fail | warn | partial
---

# Training Results — <run-tag>

## Summary
[One paragraph: what was tried, what happened.]

## Metrics
[Table or curve description; deeper detail in attached log_path.]

## Comparison
[Comparison vs baseline if applicable.]

## Notes
[Free-form analysis the agent or human captured during/after the run.]
```

The schema is versioned (`schema_version`); breaking changes increment the major version, additive changes the minor.

## Considered Options

### Option 1 — Schema in `verifier.md` agent

**Pros:** Verifier owns its inputs.

**Cons:** Couples schema evolution to agent revisions; agent bodies are not the right home for cross-cutting artifact definitions. Multiple non-verifier consumers (run-experiment writes it; check-experiment reads it; sentinel may audit it) would all reach into one agent.

### Option 2 — Schema in `llm-training-eval` skill (chosen)

**Pros:** Skill is the natural home for "what an eval result looks like." Versioned via skill updates. Multiple consumers can reach for the skill. Aligns with how `code-review` skill defines its `report-template.md` for verifier to read.

**Cons:** Cross-skill coupling between `llm-training-eval` and `verifier` (acceptable; precedent exists).

### Option 3 — Schema in `neo-cloud-abstraction` skill

**Pros:** The backend writes the artifact; the abstraction owns the lifecycle.

**Cons:** Conflates abstraction (job descriptor, lifecycle ops) with evaluation (metrics, acceptance). Different audiences. The abstraction skill is provider-focused; eval skill is methodology-focused.

## Consequences

**Positive:**
- Single source of truth for schema; updates flow through skill versioning
- Verifier remains declarative — reads what the skill says
- `/run-experiment` and `/check-experiment` share one schema reference
- Sentinel can audit `TRAINING_RESULTS.md` archives in `.ai-state/training_runs/` for completeness over time

**Negative:**
- Schema evolution requires careful versioning; verifier must handle older `schema_version` values
- Cross-skill coupling between `llm-training-eval` and `verifier` (low risk; well-bounded)

**Neutral:**
- The dual lifecycle (ephemeral + archival) preserves the autoresearch convention that most experiments are discarded; only kept runs persist
- Archive triggering (when to write `.ai-state/training_runs/<run-tag>.md`) is a `/run-experiment` decision, surfaced to the user via the existing experiment-loop "keep / discard" semantics
