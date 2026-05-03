## Eval-Driven Verification

ML training acceptance criteria use metric thresholds, not binary assertions. When
`TRAINING_RESULTS.md` exists and the plan contains metric threshold syntax, the verifier
reads recorded metrics and evaluates each criterion using a tolerance band.

**Schema reference:** `skills/llm-training-eval/references/training-results-schema.md`

### Threshold Syntax (in SYSTEMS_PLAN.md acceptance criteria)

- `val_bpb < 1.75` — strict less-than; no tolerance
- `val_bpb < 1.75 ± 0.02` — less-than with tolerance band

### PASS/FAIL/WARN Classification

- **PASS** — metric meets the criterion within tolerance
- **FAIL** — metric misses the criterion outside tolerance
- **WARN** — metric is within the tolerance band but criterion is directionally missed

### Verifier Behavior

When TRAINING_RESULTS.md is absent and the plan has metric-threshold criteria, emit
**WARN** (not FAIL) — the run may not have executed yet.

When TRAINING_RESULTS.md is present:

1. Extract recorded metrics from the `metrics:` block
2. Parse each threshold criterion
3. Apply tolerance band if declared in the plan or in `verdict.tolerance_band_applied`
4. Emit findings: `[PASS|FAIL|WARN] AC-N: val_bpb=<recorded> vs threshold=<declared>`

**Scope:** applies only when SYSTEMS_PLAN.md acceptance criteria contain metric threshold
syntax. Non-ML criteria use the standard binary PASS/FAIL protocol unchanged.

See `skills/llm-training-eval/SKILL.md` for the full tolerance-band methodology.
