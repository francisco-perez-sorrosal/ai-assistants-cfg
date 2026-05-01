# Resolved Tech Debt

<!-- Sibling of TECH_DEBT_LEDGER.md holding rows with terminal status (resolved / wontfix).
     Rows arrive via scripts/finalize_tech_debt_ledger.py migration when status transitions
     to a terminal value. Schema, lifecycle, and re-open semantics are defined canonically
     in rules/swe/agent-intermediate-documents.md § TECH_DEBT_LEDGER.md. Do not duplicate
     the schema here — the rule is the single source of truth. -->

**Schema**: 14 row fields + 1 structural `dedup_key`. See [`rules/swe/agent-intermediate-documents.md`](../rules/swe/agent-intermediate-documents.md) § `TECH_DEBT_LEDGER.md` for field definitions.

**Rows arrive here automatically** when status transitions to `resolved` or `wontfix`. The pair forms one logical namespace with `TECH_DEBT_LEDGER.md`: `id` and `dedup_key` are unique across both files. Cross-file `dedup_key` matches trigger re-open (the historical resolved row moves back to LEDGER).

| id | severity | class | direction | location | goal-ref-type | goal-ref-value | source | first-seen | last-seen | owner-role | status | resolved-by | notes | dedup_key |
|----|----------|-------|-----------|----------|---------------|----------------|--------|------------|-----------|-----------|--------|-------------|-------|-----------|
| td-001 | important | duplication | code-to-goals | commands/onboard-project.md, commands/new-project.md | code-quality |  | verifier | 2026-04-27 | 2026-04-27 | implementation-planner | resolved | 72d6db7 | Four canonical blocks (Agent Pipeline, Compaction Guidance, Behavioral Contract, Praxion Process) duplicated byte-identically across both onboarding commands; mirror discipline enforced by author + regex test, not by extraction. Proper fix: extract canonical blocks to a single source-of-truth (e.g., `claude/canonical-blocks/<name>.md`) consumed by both commands. User flagged during Step 11; refactor must cover all four blocks together to avoid mixed-state. Resolved by extracting to `claude/canonical-blocks/<slug>.md` with `scripts/sync_canonical_blocks.py` enforcing byte-identicality via pre-commit hook (build-time compilation per dec-082). | 83fa92c1f787 |
