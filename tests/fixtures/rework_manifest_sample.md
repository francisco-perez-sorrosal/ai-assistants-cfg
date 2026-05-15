# Rework Manifest — dispatch-reworks-test

Generated: 2026-05-14T12:00:00Z by verifier (report dispatch-reworks-test-2026-05-14T12).
Source: [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md). 2 rework worktrees proposed.

| # | Worktree | Agent | Severity | Tier | Class | Headline |
|---|----------|-------|----------|------|-------|----------|
| 1 | `fix-auth-expiry` | implementer | critical | standard | implementation | Expired tokens accepted silently |
| 2 | `patch-rate-limiter` | implementer | important | standard | implementation | Rate limiter off-by-one in burst window |

## Row details

### Row 1 — fix-auth-expiry

```json
{
  "id": "rw-aabbcc01",
  "worktree_name": "fix-auth-expiry",
  "target_agent": "implementer",
  "severity": "critical",
  "recommended_tier": "standard",
  "class": "implementation",
  "headline": "Expired tokens accepted silently",
  "finding_refs": ["#fail-1"],
  "td_refs": [],
  "confidence": "high",
  "dedup_against": [],
  "notes": ""
}
```

### Row 2 — patch-rate-limiter

```json
{
  "id": "rw-aabbcc02",
  "worktree_name": "patch-rate-limiter",
  "target_agent": "implementer",
  "severity": "important",
  "recommended_tier": "standard",
  "class": "implementation",
  "headline": "Rate limiter off-by-one in burst window",
  "finding_refs": ["#warn-1"],
  "td_refs": [],
  "confidence": "high",
  "dedup_against": [],
  "notes": ""
}
```
