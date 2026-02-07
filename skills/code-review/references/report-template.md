# Report Template

Canonical structure for code review reports. Used by the verifier agent (pipeline
mode) and the code-review skill (standalone mode).

## Full Template (Pipeline Mode)

```markdown
# Verification Report: [Feature Name]

## Verdict

[PASS / PASS WITH FINDINGS / FAIL]

Automated review complements but does not replace human judgment.

## Acceptance Criteria

| Criterion | Status | Evidence |
|-----------|--------|----------|
| [From SYSTEMS_PLAN.md] | PASS/FAIL/WARN | [What was observed] |

## Convention Compliance

| # | Severity | Location | Finding | Rule Reference |
|---|----------|----------|---------|----------------|
| 1 | FAIL | file.py:42 | Function exceeds 50-line ceiling (63 lines) | coding-style.md: Function Size |
| 2 | WARN | module.py:15 | Nesting depth at 4 levels (at threshold) | coding-style.md: Nesting Depth |

## Test Coverage Assessment

[Summary of test adequacy for critical paths]
[Notes on untested edge cases or missing coverage for complex logic]

## Context Artifact Completeness

[Only included when the plan contained context artifact update steps]

| Planned Update | Status | Notes |
|---------------|--------|-------|
| [From IMPLEMENTATION_PLAN.md] | Done/Missing | [What was observed] |

## Recommendations

### FAIL Findings (correction needed)

1. [Prioritized corrective actions]

### WARN Findings (review recommended)

1. [Suggested improvements]

### Merge to LEARNINGS.md

Before deleting this report, merge recurring patterns and systemic
quality issues into LEARNINGS.md.

## Scope

- Files reviewed: [count]
- Commits reviewed: [hash range or branch comparison]
- Plan steps verified: [N of M] (pipeline mode only)
- Review timestamp: [ISO 8601]
```

## Standalone Template

Omit the following sections when producing a standalone review:

- Acceptance Criteria (requires `SYSTEMS_PLAN.md`)
- Context Artifact Completeness (requires `IMPLEMENTATION_PLAN.md`)
- "Plan steps verified" from Scope
- "Merge to LEARNINGS.md" from Recommendations (no pipeline context)

The remaining sections (Verdict, Convention Compliance, Test Coverage,
Recommendations, Scope) use the same format as the full template.
