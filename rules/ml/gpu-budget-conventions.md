## GPU Budget Conventions

Every ML project step that dispatches a training run MUST declare a compute budget.
Open-ended training runs are prohibited.

### Required Fields

**In WIP.md** — each training-dispatch step must carry:

```yaml
gpu_hours_budget: <float>  # e.g., 2.0
acceptance_criteria:
  - val_bpb < 1.75                               # metric-threshold gate
  # OR
  - budget_consumed >= 2.0 GPU-hours OR val_bpb < 1.75, whichever first  # budget gate
```

**In `training_job_descriptor`** — `gpu_hours_budget` is a hard cap; the backend
MUST enforce it. Never omit this field for remote backends (SkyPilot, RunPod).

### Budget Declaration Locations

- **Project-level ceiling:** `.ai-state/gpu_budget.yaml` → `project_gpu_hours_budget`
- **Step-level budget:** WIP.md step field `gpu_hours_budget` overrides the project ceiling

See `skills/deployment/references/gpu-compute-budgeting.md` for cost-regime differences
between Mode A (owned-local, $0), Mode B (rented-local, invoice-side cost), and Mode C
(remote-dispatch with backend enforcement).

### Verifier Enforcement

An ML step without a declared `gpu_hours_budget` MUST be flagged as a **FAIL** finding
citing this rule. Budget exhaustion (`status: budget_exhausted`) is NOT a failure — it
is a normal, expected termination path that preserves checkpoints.
