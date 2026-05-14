# Rework Manifest — test-pipeline-rerun

Generated: 2026-05-14T09:00:00Z by verifier (report test-pipeline-2026-05-14T09).
Source: [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md). 1 rework worktree proposed.

| # | Worktree | Agent | Severity | Tier | Class | Headline |
|---|----------|-------|----------|------|-------|----------|
| 1 | `fix-auth-validation` | implementation-planner | suggested | standard | implementation | Session validator silently accepts expired tokens (re-emission) |

## Row details

### Row 1 — fix-auth-validation

```json
{
  "id": "rw-3b9f6ba0",
  "worktree_name": "fix-auth-validation",
  "target_agent": "implementation-planner",
  "severity": "suggested",
  "recommended_tier": "standard",
  "class": "implementation",
  "headline": "Session validator silently accepts expired tokens (re-emission)",
  "finding_refs": ["#fail-1", "#fail-2"],
  "td_refs": ["td-041"],
  "confidence": "high",
  "dedup_against": ["fix-auth-validation"],
  "notes": "Already has rework worktree; this is a re-emission"
}
```
