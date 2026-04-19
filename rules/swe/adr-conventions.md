## ADR Conventions

Architecture Decision Records live in `.ai-state/decisions/` as Markdown files with YAML frontmatter. They persist beyond `.ai-work/` cleanup and are committed to git.

### File Format

ADRs authored during a pipeline follow the **fragment-name-at-create, finalize-at-merge** path: the ADR lands as a fragment file under `.ai-state/decisions/drafts/` with a collision-safe filename and a provisional `dec-draft-<hash>` id, and is promoted to a stable `<NNN>-<slug>.md` finalized record at merge-to-main. The legacy NNN-at-create path is retained only for direct-tier user-authored ADRs that bypass a pipeline (see [Finalized ADRs (post-merge)](#finalized-adrs-post-merge) below).

#### Fragment Filename Schema

Pipeline-authored ADRs (systems-architect, implementation-planner, or any agent writing inside a Standard/Full-tier pipeline) land at:

```
.ai-state/decisions/drafts/<YYYYMMDD-HHMM>-<user>-<branch>-<slug>.md
```

**Identity derivation** (pseudocode — agents implement this before creating the file):

```
timestamp   = now_utc_formatted("YYYYMMDD-HHMM")   # filename-safe, no colons
user_raw    = git_config("user.email") or git_config("user.name") or "anon"
user_slug   = sanitize(user_raw.split("@")[0])     # username prefix from email, if email set
branch_raw  = git_rev_parse("--abbrev-ref", "HEAD") or "detached"
branch_slug = sanitize(branch_raw)
slug        = kebab_case(decision_title)
filename    = f"{timestamp}-{user_slug}-{branch_slug}-{slug}.md"
id          = f"dec-draft-{sha1(filename)[:8]}"
```

`sanitize(s)` lowercases and strips to `[a-z0-9-]` (replacing any run of other characters with a single `-`) and caps length at 40 characters. When both `user.email` and `user.name` are unset, use `anon` — never fabricate identity.

**Frontmatter at creation**: `id: dec-draft-<8-char-hash>`, `status: proposed`. All other fields (see the [Frontmatter](#frontmatter) table) are populated as usual.

**Cross-reference convention within drafts**: draft-to-draft `supersedes`, `superseded_by`, `re_affirms`, and `re_affirmed_by` values use `dec-draft-<hash>` — never a speculative `dec-NNN`. The [Finalize Protocol](#finalize-protocol) rewrites these to `dec-NNN` atomically at merge-to-main.

**PII note**: the fragment filename contains a sanitized email-username prefix. This is acceptable for internal project state but is not a secret — treat fragment filenames the same way as commit-author metadata, not as redacted data. Teams with stricter privacy requirements can substitute a short hash of the email address for the username prefix.

**Collision avoidance**: minute-precision timestamp + user + branch makes collisions effectively impossible in normal use. If two drafts with the same minute, user, branch, and slug do land, append `-2`, `-3`, ... to the slug at write time.

#### Finalized ADRs (post-merge)

After finalize runs at merge-to-main (see [Finalize Protocol](#finalize-protocol)), the ADR lives at:

```
.ai-state/decisions/<NNN>-<slug>.md
```

**Naming**: `<NNN>-<slug>.md` — zero-padded 3-digit sequence number, kebab-case slug. The `<NNN>` is assigned by the finalize script at merge-to-main, not at creation; pipeline-authored ADRs never pick their own `<NNN>`.

**Direct-tier user-authored ADRs** (no pipeline, no agent involvement) MAY still be created directly at `.ai-state/decisions/<NNN>-<slug>.md` with the next sequential `<NNN>` assigned by scanning existing filenames (ignoring `drafts/`). This legacy path exists for simplicity when a human writes a one-off decision outside a pipeline; it is deprecated for all agent-authored and pipeline-authored ADRs.

#### Frontmatter

The frontmatter schema is shared between draft and finalized ADRs. Only the `id` value format differs between the two stages (`dec-draft-<8-char-hash>` during draft; `dec-NNN` after finalize). Cross-reference fields (`supersedes`, `superseded_by`, `re_affirms`, `re_affirmed_by`) likewise carry `dec-draft-<hash>` values during the draft stage and `dec-NNN` values after finalize.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | `dec-draft-<8-char-hash>` in drafts; `dec-NNN` after finalize |
| `title` | string | Yes | Short decision title |
| `status` | string | Yes | `proposed` / `accepted` / `superseded` / `rejected` / `re-affirmation` |
| `category` | string | Yes | `architectural` / `behavioral` / `implementation` / `configuration` |
| `date` | string | Yes | ISO 8601 date (`YYYY-MM-DD`) |
| `summary` | string | Yes | One-line description for index and scanning |
| `tags` | list | Yes | Lowercase topic tags for filtering |
| `made_by` | string | Yes | `agent` / `user` |
| `agent_type` | string | When agent | Which agent (e.g., `systems-architect`) |
| `pipeline_tier` | string | No | `direct` / `lightweight` / `standard` / `full` / `spike` |
| `affected_files` | list | No | Paths impacted by the decision |
| `affected_reqs` | list | No | REQ IDs linked to the decision |
| `supersedes` | string | No | id of prior decision (`dec-draft-<hash>` in drafts; `dec-NNN` after finalize) |
| `superseded_by` | string | No | id of replacing decision (same id-form rule) |
| `re_affirms` | string | No | id of prior decision this ADR re-affirms without superseding (same id-form rule) |
| `re_affirmed_by` | list | No | ids of later ADRs that re-affirmed this decision (same id-form rule) |

**Body sections** (after frontmatter):

1. **Context** -- what prompted the decision (problem, constraint, opportunity)
2. **Decision** -- what was decided (clear, direct statement)
3. **Considered Options** -- alternatives with pros/cons (subsections per option)
4. **Consequences** -- positive and negative outcomes
5. **Prior Decision** -- only when superseding; summarizes what changed and why

### Supersession Protocol

When a new ADR supersedes an existing one:

1. Set `supersedes: <target-id>` in the **new** ADR frontmatter (`dec-draft-<hash>` while both are drafts, `dec-NNN` when the target is finalized)
2. Set `superseded_by: <new-id>` in the **old** ADR frontmatter (same id-form rule)
3. Change the old ADR status to `superseded`
4. Add a `## Prior Decision` section in the new ADR body
5. `DECISIONS_INDEX.md` regenerates automatically at finalize — do not manually invoke the index-regeneration script

### Re-affirmation Protocol

When a new ADR re-affirms an existing one without superseding it (a re-opening was considered and rejected for lack of new evidence):

1. Set `status: re-affirmation` on the **new** ADR (signals meta-decision — a decision *about* another decision)
2. Set `re_affirms: <target-id>` in the **new** ADR frontmatter (same draft-vs-finalized id-form rule as Supersession)
3. Append `<new-id>` to the **old** ADR's `re_affirmed_by` list (create the list if absent)
4. **Do not** change the old ADR's status — it stays `accepted`; no `superseded_by` is set
5. Add a `## Prior Decision` section in the new ADR body explaining what was considered and why the prior decision still holds; name the evidence that would be required to justify a future supersession
6. `DECISIONS_INDEX.md` regenerates automatically at finalize

Re-affirmation is intentionally stronger than silent concurrence (it forces a public record of the re-opening) and gentler than supersession (the prior decision is untouched). Use it when a prior decision is challenged, re-examined, and found still correct — not as a routine acknowledgment.

### Finalize Protocol

Finalize promotes drafts in `.ai-state/decisions/drafts/` to finalized `<NNN>-<slug>.md` records at merge-to-main. It is invoked automatically by the post-merge git hook and by `/merge-worktree`; operators may also trigger it manually via a finalize script. The protocol is **idempotent** — running twice on the same state is a no-op — so duplicated invocations from hook + command are safe.

1. **Draft detection.** Identify drafts added in the merged range (`<merge-base>..HEAD`) under `.ai-state/decisions/drafts/`. A manual-branch mode detects drafts added by a named branch. A dry-run mode prints the planned changes without writing.
2. **NNN assignment.** For each detected draft, assign the next sequential `<NNN>` by scanning `.ai-state/decisions/` for the highest existing `<NNN>-<slug>.md` value, ignoring the `drafts/` subdirectory entirely. Assignments follow filename-sort order across the batch so the sequence is deterministic.
3. **File rename and `id` rewrite.** Rename `.ai-state/decisions/drafts/<fragment>.md` to `.ai-state/decisions/<NNN>-<slug>.md` (slug extracted as the trailing `-<slug>.md` component of the fragment filename). Rewrite the frontmatter `id:` field from `dec-draft-<hash>` to `dec-NNN`.
4. **Cross-reference rewrite.** Rewrite every `dec-draft-<hash>` occurrence (for each promoted draft) to its newly assigned `dec-NNN` across a bounded set of locations:
   - All ADR files under `.ai-state/decisions/` — both drafts still in flight and finalized records. Frontmatter fields (`supersedes`, `superseded_by`, `re_affirms`, `re_affirmed_by`) and inline body references (`[dec-draft-<hash>]` or bare `dec-draft-<hash>`).
   - All `.ai-work/*/LEARNINGS.md` files.
   - All `.ai-work/*/SYSTEMS_PLAN.md` and `.ai-work/*/IMPLEMENTATION_PLAN.md` files.
   - `.ai-state/specs/SPEC_<name>_YYYY-MM-DD.md` files matching the current pipeline's task slug.

   The walk scope is bounded by design — finalize does not sweep the full repo for text replacement.
5. **Index regeneration.** After all drafts in the batch promote, `DECISIONS_INDEX.md` regenerates to reflect the new finalized records. Drafts are excluded from the index by construction; the index lists only finalized `<NNN>-<slug>.md` files.

Concurrency safety: finalize acquires an advisory file lock before any writes so concurrent post-merge hook invocations serialize cleanly. Exit codes: `0` for success or no-op; non-zero only when manual intervention is needed (e.g., an unresolvable filename collision). The protocol deliberately avoids rewriting arbitrary repository text; the bounded walk scope is the contract.

### Who Writes ADRs

| Agent | When | Scope | Destination |
|-------|------|-------|-------------|
| systems-architect | Phase 4 (trade-off analysis) | Significant trade-offs: system boundaries, data model, technology selection, security | `.ai-state/decisions/drafts/` (fragment) |
| implementation-planner | Step decomposition | Decisions affecting step ordering, module structure, approach | `.ai-state/decisions/drafts/` (fragment) |
| user | Direct tier or manual | Any decision worth preserving | `.ai-state/decisions/drafts/` preferred; `<NNN>-<slug>.md` acceptable for direct-tier, no-pipeline authoring |

All ADR authors also record decisions in `LEARNINGS.md ### Decisions Made` using the structured format. While a pipeline is in flight, `LEARNINGS.md` carries `dec-draft-<hash>` references; finalize rewrites these to `dec-NNN` at merge-to-main.

### Agent Writing Protocol

1. Derive author identity from `git config` (see the [Fragment Filename Schema](#fragment-filename-schema) for the full pseudocode): prefer the username prefix of `user.email`, fall back to `user.name`, then `anon`; sanitize to `[a-z0-9-]` and cap at 40 chars.
2. Build the fragment filename `<YYYYMMDD-HHMM>-<user>-<branch>-<slug>.md` using the current UTC timestamp, sanitized branch (`git rev-parse --abbrev-ref HEAD`), and kebab-case slug of the decision title.
3. Compute `id: dec-draft-<sha1(filename)[:8]>`.
4. Create `.ai-state/decisions/drafts/<fragment-filename>.md` using the Write tool with frontmatter `id: dec-draft-<hash>` and `status: proposed` (plus the rest of the schema from the [Frontmatter](#frontmatter) table).
5. Cross-references between drafts use `dec-draft-<hash>` values — the [Finalize Protocol](#finalize-protocol) rewrites them to `dec-NNN` at merge-to-main.
6. Record the decision compactly in `LEARNINGS.md ### Decisions Made`, citing the draft id (`(dec-draft-<hash>)`). Finalize rewrites these references too.
7. Do **not** manually invoke the index-regeneration script — `DECISIONS_INDEX.md` regenerates automatically at finalize.

### Discovery Protocol

1. Read `.ai-state/decisions/DECISIONS_INDEX.md` for an overview of finalized ADRs
2. Grep for matching `category`, `tags`, or `affected_files` in the index table
3. For in-flight work, also scan `.ai-state/decisions/drafts/` — drafts are not indexed but are authoritative during the pipeline that authored them
4. Read full ADR files for matching decisions
5. Fallback (if index missing): `Glob .ai-state/decisions/[0-9]*.md` + `Glob .ai-state/decisions/drafts/*.md` + Grep frontmatter

### Consumption

| Consumer | Purpose |
|----------|---------|
| sentinel | DL01-DL05: validate ADR format, frontmatter, body, index consistency, frequency — for both draft and finalized ADRs |
| skill-genesis | Recurring decision patterns across features |
| verifier | Cross-reference `affected_reqs` against traceability matrix |
| systems-architect | Brownfield baseline for prior feature decisions |

### Relationship to LEARNINGS.md

- `LEARNINGS.md` is broader: gotchas, patterns, edge cases, tech debt, decisions
- ADR files are narrower: decisions only, persistent, human-browsable
- Decisions appear in both -- `LEARNINGS.md` is ephemeral; ADR files persist
- Draft-stage `dec-draft-<hash>` references in `LEARNINGS.md` are rewritten to `dec-NNN` at finalize alongside the ADR files themselves

### Migration — historical ADRs

Pre-existing finalized ADRs (those already at `.ai-state/decisions/<NNN>-<slug>.md` before the fragment scheme rolled out) remain **untouched**. Their filenames, `id: dec-NNN` frontmatter, and cross-references are preserved as-is. The fragment-name-at-create scheme applies only to newly authored ADRs from the rollout forward; no retroactive renumbering runs over historical records.
