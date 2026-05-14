---
id: dec-181
title: TECH_DEBT_LEDGER rework-worktree linkage via notes-field suffix; main agent owns the in-flight status flip
status: accepted
category: architectural
date: 2026-05-14
summary: Encode the rework worktree name in the existing `notes` field with stable suffix `// in-flight via rework worktree <name>` (no schema change). The main agent (orchestrator) is the writer that flips status from open to in-flight when creating a rework worktree, per ledger writer policy.
tags: [tech-debt-ledger, rework, linkage, notes-field, orchestrator-writer]
made_by: agent
agent_type: systems-architect
branch: worktree-verifier-rework-loop
pipeline_tier: standard
affected_files:
  - .ai-state/TECH_DEBT_LEDGER.md
  - rules/swe/swe-agent-coordination-protocol.md
  - skills/software-planning/references/tech-debt-ledger.md
---

## Context

When the main agent creates a rework worktree from a manifest row whose `td_refs` lists one or more `td-NNN` rows, those ledger rows transition from `open` to `in-flight`. Two design questions:

1. **Linkage shape**: how does a `td-NNN` row record which rework worktree is addressing it? The existing 14-field schema has no field for this. Options: extend the schema with a new `rework-ref` field, encode it in the existing `notes` field, or skip linkage entirely.

2. **Writer identity**: who flips the `status` from `open` to `in-flight`? The ledger writer policy authorizes only four agents: verifier, sentinel, orchestrator (under explicit user direction), and architect-validator. The verifier emits the manifest *proposing* reworks; the main agent creates the worktrees *enacting* reworks; the dispatched agent (architect or planner) actually does the work. Which one writes the status change?

**Activation:** yes (schema-impact decision, ledger-integrity concern, writer-policy clarification). Lenses applied: Simplicity (no schema change), Hard-to-misuse (status reflects reality), Future-proof (notes-field encoding is reversible if a schema field is needed later), Correctness (writer identity matches the side-effect that creates the state).

## Decision

**Linkage: notes-field suffix.** When the main agent flips a `td-NNN` row to `in-flight`, it appends the stable suffix `// in-flight via rework worktree <name>` to the row's `notes` field (where `<name>` is the rework worktree's kebab-case slug). No schema change; the suffix is greppable; the dedup-key formula is unaffected because `notes` is not part of the `dedup_key` computation.

When the rework merges and `status` transitions to `resolved`, the suffix is removed in the same edit (the row migrates to `TECH_DEBT_RESOLVED.md` via `scripts/finalize_tech_debt_ledger.py`; `resolved-by` carries the merge commit SHA, which is the canonical post-hoc linkage).

**Writer: orchestrator (main agent), not verifier and not dispatched agent.** The `tech-debt-ledger.md` § Writers section already authorizes the orchestrator to write "under explicit user direction." This feature codifies that direction: when the user (implicitly, by not vetoing a manifest row) approves a rework, the main agent's worktree-creation step includes the ledger edit.

Status timing:
- `open` → `in-flight`: at worktree creation by main agent (atomic with `EnterWorktree` + `VERIFIER_FINDINGS.md` write).
- `in-flight` → `resolved`: at parent-pipeline re-verification (the verifier sees the corrective work via re-detection logic — same `dedup_key` no longer matches a current finding — and flips status; `resolved-by` is populated with the rework worktree's merge commit SHA).

## Considered Options

### Linkage: Option A — Add `rework-ref` field to schema

Pros: semantic clarity; queryable without parsing notes; matches the canonical ledger pattern.

Cons: schema change (14 → 15 fields); requires updates to `skills/software-planning/references/tech-debt-ledger.md`, `scripts/finalize_tech_debt_ledger.py` dedupe logic, and potentially sentinel DL01–DL05 checks; the field is rework-loop-specific (no other feature would use it), violating the ledger's general-purpose design.

Rejected — too much downstream surface for too little gain.

### Linkage: Option B — Notes-field suffix (chosen)

Pros: zero schema change; the suffix is greppable, parseable, and visible in the rendered table; reversible (a future migration to a typed field can scrape the suffix); doesn't pollute the dedup-key.

Cons: convention-not-schema; a future writer who forgets the suffix won't be caught by sentinel; the notes field's prose discipline is loosened slightly.

**Chosen.** The convention is named in REQ-RWK-11; the verifier and main agent are the only writers; the suffix's stable shape is greppable enough to catch drift in a sentinel pass if needed.

### Linkage: Option C — Skip linkage entirely

Pros: simplest.

Cons: the user listing open in-flight debt (`grep 'in-flight' .ai-state/TECH_DEBT_LEDGER.md`) has no way to find where the work is happening. The merge commit (in `resolved-by`) is post-hoc — useless during the in-flight window.

Rejected.

### Writer: Option α — Verifier writes in-flight when emitting the manifest

Pros: verifier is already an authorized writer; ledger edit co-locates with the manifest write.

Cons: a manifest entry is a *proposal* — the user can veto a row before the main agent creates the worktree. Writing `in-flight` at manifest-write time would be wrong if the user vetoes.

Rejected.

### Writer: Option β — Main agent writes in-flight at worktree creation (chosen)

Pros: status accurately reflects reality (only `in-flight` once a worktree exists); the main agent is the one creating the side effect; the orchestrator-writer authorization in `tech-debt-ledger.md` § Writers covers this with "under explicit user direction" — the user's approval of the manifest row IS that direction.

Cons: orchestrator writes are intentionally rare per ledger policy (verifier/sentinel are the canonical producers).

**Chosen.** REQ-RWK-11 codifies the orchestrator's writer authority for this specific operation.

### Writer: Option γ — Dispatched agent writes in-flight during its own Phase 1

Pros: keeps the orchestrator out of the ledger.

Cons: requires the dispatched agent to know about the parent's ledger entries; bleeds context across worktree boundaries; the architect/planner Phase 1 would need new logic — violating the load-bearing hypothesis of `dec-175`.

Rejected.

## Consequences

**Positive:**

- No schema change; downstream tools (`finalize_tech_debt_ledger.py`, sentinel DL checks) are unaffected.
- The active ledger surface remains lean (14 fields).
- A grep over the LEDGER reveals in-flight reworks at a glance.
- Worktree concurrency (per `tech-debt-ledger.md` § Worktree concurrency) is unaffected — status-in-place updates compose with the existing `fcntl` lock and post-merge dedupe.

**Negative:**

- The suffix convention is not schema-enforced; a future writer who omits it gets no automated warning. Mitigation: only two writers (verifier and main agent), both governed by REQ-RWK-11 and explicit prompt text.
- The orchestrator now has one more ledger-write code path. Acceptable per ledger writer policy.

**Mitigation:**

- If the suffix convention drifts, a sentinel DL check can be added later to detect rows with `status: in-flight` whose `notes` lacks the suffix (sentinel adds checks routinely; this is a small additive change).
- If a future Praxion feature needs typed rework-linkage at scale, migration from suffix-encoding to a typed `rework-ref` field is a single-pass script over the ledger.
