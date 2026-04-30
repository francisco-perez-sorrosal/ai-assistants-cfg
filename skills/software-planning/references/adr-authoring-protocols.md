# ADR Authoring Protocols

Procedural protocols for creating and maintaining Architecture Decision Records under `.ai-state/decisions/`. Reference material for the [Software Planning](../SKILL.md) skill. For the file format, frontmatter schema, naming conventions, and finalize protocol, see the [adr-conventions rule](../../../rules/swe/adr-conventions.md) — that is the canonical source of truth.

## ADR Creation Protocol (fragment-name-at-create)

Pipeline-authored ADRs land as **fragment files** under `.ai-state/decisions/drafts/` with a provisional `dec-draft-<8-char-hash>` id. Fragments are promoted to stable `<NNN>-<slug>.md` finalized records at merge-to-main by the post-merge finalize step. Agents do **not** assign `<NNN>` themselves.

When a decision-making agent (systems-architect, implementation-planner) records a decision in `LEARNINGS.md ### Decisions Made`:

1. **Derive author identity** from `git config` — prefer the username prefix of `user.email`, fall back to `user.name`, then `anon`. Sanitize to `[a-z0-9-]` and cap at 40 characters. Full pseudocode lives in the [adr-conventions rule](../../../rules/swe/adr-conventions.md#fragment-filename-schema).
2. **Build the fragment filename** `<YYYYMMDD-HHMM>-<user>-<branch>-<slug>.md`, where `<slug>` is the kebab-case decision title and `<branch>` is the sanitized current branch (`git rev-parse --abbrev-ref HEAD`).
3. **Compute the provisional id** as `dec-draft-<sha1(filename)[:8]>`.
4. **Create the fragment** at `.ai-state/decisions/drafts/<fragment-filename>.md` using the Write tool, with frontmatter `id: dec-draft-<hash>` and `status: proposed` plus the full schema fields.
5. **Cross-references between drafts** use `dec-draft-<hash>` values for `supersedes` / `superseded_by` / `re_affirms` / `re_affirmed_by`. Finalize rewrites these to `dec-NNN` at merge-to-main.
6. **Record the decision** in `LEARNINGS.md ### Decisions Made` citing `(dec-draft-<hash>)`. Finalize rewrites this reference too.
7. **Do not** manually invoke any index-regeneration script — `DECISIONS_INDEX.md` regenerates automatically at finalize.

## Who Creates ADRs

Not all agents create ADR fragments. The division follows decision-making authority:

| Agent | Creates ADR fragments | Records in LEARNINGS.md |
|-------|----------------------|-------------------------|
| systems-architect | Yes | Yes |
| implementation-planner | Yes | Yes |
| implementer | No | Yes |
| test-engineer | No | Yes |
| verifier | No | Yes |
| sentinel | No | N/A |

Implementers, test-engineers, and verifiers record decisions in `LEARNINGS.md` only — the planner or architect persists significant decisions as ADR fragments.

User-authored direct-tier ADRs (no pipeline involvement) MAY be created directly at `.ai-state/decisions/<NNN>-<slug>.md` with a manually-assigned `<NNN>`, but the fragment scheme is preferred even for direct-tier authoring because it avoids `<NNN>` collisions when work is in flight on multiple branches.

## Supersession Protocol

When a new decision replaces a prior one:

1. Set `supersedes: <target-id>` in the **new** ADR frontmatter — `dec-draft-<hash>` while both are drafts; `dec-NNN` when the target is finalized.
2. Set `superseded_by: <new-id>` in the **old** ADR frontmatter (same id-form rule).
3. Change the old ADR status to `superseded`.
4. Add a `## Prior Decision` section in the new ADR body explaining what changed and why.
5. `DECISIONS_INDEX.md` regenerates automatically at finalize — do not manually invoke.

## Re-affirmation Protocol

When a new ADR re-affirms a prior one without superseding it (a re-opening was considered and rejected for lack of new evidence):

1. Set `status: re-affirmation` on the new ADR — signals a meta-decision about another decision.
2. Set `re_affirms: <target-id>` in the new ADR frontmatter (same id-form rule as Supersession).
3. Append `<new-id>` to the old ADR's `re_affirmed_by` list (create the list if absent).
4. **Do not** change the old ADR's status — it stays `accepted`; no `superseded_by` is set.
5. Add a `## Prior Decision` section in the new ADR explaining what was considered and why the prior decision still holds; name the evidence that would justify a future supersession.

Re-affirmation is stronger than silent concurrence (it forces a public record of the re-opening) and gentler than supersession (the prior decision is untouched). Use it when a prior decision is challenged, re-examined, and found still correct — not as a routine acknowledgment.

## Finalize at Merge-to-Main

At merge-to-main, the post-merge finalize step promotes drafts in `.ai-state/decisions/drafts/` to finalized `<NNN>-<slug>.md` records. The protocol is **idempotent** (running twice is a no-op) and rewrites every `dec-draft-<hash>` cross-reference within a bounded scope (other ADR files, in-flight `LEARNINGS.md` files, in-flight planning documents, archived spec files matching the current pipeline's task slug).

For the full finalize protocol — draft detection, NNN assignment, file rename, cross-reference rewrite scope, and concurrency safety — see the [adr-conventions rule](../../../rules/swe/adr-conventions.md#finalize-protocol).

Agents do not run finalize manually. The post-merge git hook and the merge-worktree command both invoke it; the protocol's idempotency makes duplicate invocations safe.

## Spec Archival Cross-Reference

During end-of-feature spec archival, the implementation-planner cross-references decisions from `LEARNINGS.md ### Decisions Made` with ADR files in `.ai-state/decisions/`. The archived spec's `## Key Decisions` section should link to relevant ADR files for full context.

While a pipeline is in flight, both `LEARNINGS.md` and the archived spec carry `dec-draft-<hash>` references; these are rewritten to `dec-NNN` at merge-to-main alongside the ADR fragment promotions.

## End-of-Feature Decision Verification

During the end-of-feature workflow, verify consistency between:

- Decisions in `LEARNINGS.md ### Decisions Made`
- ADR fragments under `.ai-state/decisions/drafts/` (in flight) or finalized records under `.ai-state/decisions/` (post-merge)

Check for decisions recorded in `LEARNINGS.md` but missing as ADR fragments (creation protocol was not followed), and ADR fragments without corresponding `LEARNINGS.md` entries (unusual but not necessarily an error).
