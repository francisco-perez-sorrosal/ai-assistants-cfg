---
paths:
  - "runs/**"
  - "experiments/**"
  - "program.md"
---

## Experiment Tracking Conventions

Conventions for ML projects that use iterative experiment loops. Loaded when working
on files under `runs/`, `experiments/`, or the project's `program.md`.

### Tracker Declaration

The experiment tracker is declared in `program.md` under a `tracker:` key:

```markdown
## Tracker

mlflow  # or: wandb
```

Absence of the `tracker:` key defaults to **MLflow**. See
`skills/experiment-tracking/SKILL.md` for MLflow vs W&B selection guidance.

### Run Logging Requirements

- Every training run MUST be logged to the configured experiment tracker
- Hyperparameter changes between runs MUST be tracked as **distinct runs**, not run
  overrides — overwriting a prior run destroys the comparison baseline
- The run start and end must be explicitly recorded; partial runs are logged with
  `status: failed` or `status: budget_exhausted`

### `run_tag` Cross-Reference

`run_tag` in `TRAINING_RESULTS.md` MUST match the tracker's run identifier (MLflow
run name or W&B run ID) so results are cross-referenceable across the two systems.
See `skills/experiment-tracking/references/mlflow-integration.md` and
`skills/experiment-tracking/references/wandb-integration.md` for mapping patterns.

### `program.md` Vocabulary

`program.md` is the **project-local meta-prompt** for the autonomous experiment loop —
a sibling of `CLAUDE.md` focused on guiding the training cycle rather than the
development session. It is:

- NOT documentation (not a README or design spec)
- NOT a behavioral spec (not a SYSTEMS_PLAN.md)
- NOT an ADR or skill

It is recognized by `implementation-planner` and `verifier` alongside `CLAUDE.md`.
See `skills/ml-training/SKILL.md` for the full `program.md` vocabulary and lifecycle.

### Experiment Directory Convention

Experiment artifacts live under `experiments/<run-tag>/`:

```text
experiments/
  <run-tag>/
    config.yaml      # hyperparameter snapshot at run start
    metrics.jsonl    # per-step metric log
    checkpoint_path  # path to best checkpoint (may be gitignored)
```

Checkpoint files (`.pt`, `.bin`, `.safetensors`) are gitignored by default.
Only `config.yaml`, `metrics.jsonl`, and `TRAINING_RESULTS.md` are committed.
