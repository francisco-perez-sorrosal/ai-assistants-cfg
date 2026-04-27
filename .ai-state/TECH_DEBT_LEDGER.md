# Technical Debt Ledger

<!-- Living, append-only ledger of grounded debt findings.
     Producers: verifier (per-change Phase 5/5.5), sentinel (repo-wide TD dimension).
     Consumers: systems-architect, implementation-planner, implementer, test-engineer, doc-engineer.
     Schema, owner-role heuristic, worktree-merge dedupe semantics, and lifecycle conventions
     are defined canonically in rules/swe/agent-intermediate-documents.md § TECH_DEBT_LEDGER.md.
     Do not duplicate the schema here — the rule is the single source of truth. -->

**Schema**: 14 row fields + 1 structural `dedup_key`. See [`rules/swe/agent-intermediate-documents.md`](../rules/swe/agent-intermediate-documents.md) § `TECH_DEBT_LEDGER.md` for field definitions, enum values, the owner-role heuristic, and the post-merge dedupe contract.

**Append new rows at the end of the table.** Consumers update `status`, `resolved-by`, and `last-seen` in place. Rows are never deleted.

| id | severity | class | direction | location | goal-ref-type | goal-ref-value | source | first-seen | last-seen | owner-role | status | resolved-by | notes | dedup_key |
|----|----------|-------|-----------|----------|---------------|----------------|--------|------------|-----------|-----------|--------|-------------|-------|-----------|
| td-001 | important | duplication | code-to-goals | commands/onboard-project.md, commands/new-project.md | code-quality |  | verifier | 2026-04-27 | 2026-04-27 | implementation-planner | open |  | Four canonical blocks (Agent Pipeline, Compaction Guidance, Behavioral Contract, Praxion Process) duplicated byte-identically across both onboarding commands; mirror discipline enforced by author + regex test, not by extraction. Proper fix: extract canonical blocks to a single source-of-truth (e.g., `claude/canonical-blocks/<name>.md`) consumed by both commands. User flagged during Step 11; refactor must cover all four blocks together to avoid mixed-state. | 83fa92c1f787 |
