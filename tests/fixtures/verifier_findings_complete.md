# Rework: Session validator silently accepts expired tokens

## Problem

The session validator in `src/auth/session.py::validate()` accepts tokens whose
`expires_at` is earlier than `time.time()` and returns a success result. Two
verification findings flag this as a contract violation.

## Scope

### In scope
- `src/auth/session.py` — the validator function and its immediate helpers
- `tests/auth/test_session.py` — add or update tests that assert the 401 path

### Out of scope
- The `require_session` decorator chain — works correctly assuming the validator
  honors its contract
- The token-cache layer — its own rework worktree covers it

## Evidence

- `src/auth/session.py:47` — `validate()` returns success without checking `expires_at` — from `[VERIFICATION_REPORT.md#fail-1]`
- `tests/auth/test_session.py:23` — `test_expired_token_returns_401` is skipped — from `[VERIFICATION_REPORT.md#fail-2]`

## Success Criteria

- [ ] `validate()` raises an error when `expires_at` is past
- [ ] `test_expired_token_returns_401` is un-skipped and passes
- [ ] No new TODO markers introduced

## Ledger Links

- td-041 — Session validator expiry contract — `[TECH_DEBT_LEDGER.md#td-041]`

## Suggested Tier

`standard` — two findings cluster, one core file, one test file.

## Provenance

- Source report: `[VERIFICATION_REPORT.md](../../../auth-flow/.ai-work/auth-flow/VERIFICATION_REPORT.md)`
- Parent worktree: `auth-flow`
- Parent task slug: `auth-flow`
- Rework ID: `rw-3b9f6ba0`
- Verifier confidence: `high`
- Generated: 2026-05-14T08:00:00Z
