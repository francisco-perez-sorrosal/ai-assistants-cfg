---
id: dec-draft-39d5e378
title: Diátaxis-aligned DaC companion as reference under doc-management with per-mode fence-regenerability rules
status: proposed
category: configuration
date: 2026-05-01
summary: 'Ship skills/doc-management/references/diataxis-modes.md as a single on-demand reference that maps the four Diátaxis modes (Tutorial / How-to / Reference / Explanation) to explicit aac:generated vs aac:authored fence regenerability rules; light-touch updates to skills/doc-management/SKILL.md and agents/doc-engineer.md Phase 1; no new skill, no always-loaded cost.'
tags: [skill-reference, diataxis, dac, fence, doc-management, doc-engineer]
made_by: agent
agent_type: systems-architect
pipeline_tier: standard
affected_files:
  - skills/doc-management/references/diataxis-modes.md
  - skills/doc-management/SKILL.md
  - agents/doc-engineer.md
re_affirms: dec-draft-237a18f6
---

## Context

The v1 fence convention (`dec-098`) makes generated-vs-authored content mechanically distinguishable in markdown via `<!-- aac:generated -->` / `<!-- aac:authored -->` regions. The convention answers *how* to mark content but does not answer *what content goes in which fence kind* — that is a documentation methodology question, not a syntax question.

[Diátaxis](https://diataxis.fr/) is a widely-adopted documentation framework that classifies content into four modes by reader intent:

- **Tutorial** — learning-oriented (study).
- **How-to** — task-oriented (do).
- **Reference** — information-oriented (look up).
- **Explanation** — understanding-oriented (think).

Without explicit guidance, doc authors and the `doc-engineer` agent place content arbitrarily inside fences, producing two failure modes: rationale narrative inside `aac:generated` fences (which the validator will eventually try to drift-check against a non-existent source), and component inventories inside `aac:authored` fences (which the validator will not drift-check against the LikeC4 model — silent drift). Pairing Diátaxis modes with explicit fence-regenerability rules eliminates both failure modes.

## Decision

Ship `skills/doc-management/references/diataxis-modes.md` as a single on-demand reference file (no new skill).

The reference defines:

1. **The four-mode taxonomy** with one paragraph per mode covering: when to use this mode, what fence to choose, common pitfalls.
2. **A canonical mapping table** assigning each mode an explicit fence-regenerability rule:

| Mode | Reader intent | Default fence | Notes |
|------|---------------|---------------|-------|
| Tutorial | "Help me learn by doing" | `aac:authored` | Learning prose; code samples are illustrative, not regenerable |
| How-to | "Help me do this task" | `aac:authored` (mostly) | Procedure prose authored; reference embeds may use `aac:generated` |
| Reference | "Tell me what's there" | `aac:generated` | Component tables, deployment topology, API matrices, configuration option lists |
| Explanation | "Help me understand why" | `aac:authored` | Rationale, trade-offs, historical context, design narrative |

3. **A "How modes pair with the AaC fence convention" section** explaining that the fence kind is the *machine-detectable* signal; the Diátaxis mode is the *intent* that justifies the fence choice. The validator does not know which mode a section belongs to — that is the author's responsibility — but choosing the right mode prevents intent/contract drift.
4. **Worked examples** showing each mode with the appropriate fence convention.

Update `skills/doc-management/SKILL.md` with one short section (≤15 lines) titled "Diátaxis Modes for Architecture Docs" that:
- Names the four modes in one sentence.
- Embeds the canonical mapping table.
- Points readers to the new reference for full guidance.

Update `agents/doc-engineer.md` Phase 1 (Scope Assessment) with one paragraph (≤6 lines) instructing the agent to consult the new reference when assessing or authoring an architecture document.

## Considered Options

### Option 1 — Reference under `doc-management` (chosen)

**Pros:** doc-management is already the home for documentation methodology. Diátaxis is a methodology overlay, not a separate domain. Reference loads on-demand from doc-engineer's existing skill list. No new skill catalog entry. Token-budget impact zero.

**Cons:** doc-engineer's reference catalog grows by one entry. Acceptable; references are progressive-disclosure.

### Option 2 — New skill `skills/diataxis-companion/`

**Pros:** Strong topical isolation; clear discoverability for non-doc-engineer consumers.

**Cons:** Diátaxis-without-DaC-context is too narrow to justify a top-level skill; the value comes from pairing it with the AaC fence convention, which is a doc-management concern. Rejected.

### Option 3 — Inline in `skills/doc-management/SKILL.md`

**Pros:** No new file.

**Cons:** Violates progressive disclosure: doc-management's SKILL.md already covers six documentation types, cross-reference patterns, freshness, and the four references it points to; adding a Diátaxis section in-body bloats activation cost. The reference pattern is the established way to add depth without bloating SKILL.md. Rejected.

### Option 4 — New rule `rules/writing/diataxis-conventions.md`

**Pros:** Path-scoped to architecture markdown.

**Cons:** Diátaxis is procedural (here's how to choose a mode for a given content goal), not a constraint (here's what's forbidden). Rules encode declarative constraints; this is a procedural guide. Misplacement. Rejected.

## Consequences

**Positive:**

- Doc authors and the doc-engineer agent get an explicit mapping from content intent to fence regenerability rule.
- The mapping is mechanically consistent with the v1 fence validator: any content placed in an `aac:generated` fence will be drift-checked; content in `aac:authored` will not. Choosing the wrong fence (mode/fence mismatch) produces a self-correcting signal — either the validator drifts immediately on arbitrary prose inside a generated fence, or the validator never checks regenerable content inside an authored fence (caught by the architect-validator's structural pass when the model adds an element the doc never reflects).
- Zero always-loaded token cost: reference file loads on demand; SKILL.md update is small.

**Negative:**

- Authors unfamiliar with Diátaxis must follow the link to https://diataxis.fr/ for full context. Mitigated by the reference's worked examples covering each mode.
- The mapping is opinionated; some content does not cleanly fit one mode (e.g., a "design rationale plus component inventory" section). Authors must split such content across two fenced regions, one per mode. Documented as a "common pitfall".

**Operational:**

- Reference file location is `skills/doc-management/references/diataxis-modes.md`, joining the existing five reference files under that skill (`cross-reference-patterns.md`, `documentation-types.md`, `diagram-conventions.md`, `advanced-markdown-patterns.md`, `assets/ARCHITECTURE_GUIDE_TEMPLATE.md`).
- The doc-engineer agent file gains one paragraph; no broader prompt restructure.
- The SKILL.md update is small enough to not require a new staleness marker; the existing SKILL.md does not declare `staleness_sensitive_sections:`. The new section can be added without changing that policy.
- Library-version verification: Diátaxis is a methodology, not a library. The reference cites https://diataxis.fr/ as the authoritative source; no version pinning applies.

## Prior Decision

This ADR re-affirms `dec-draft-237a18f6` (the golden-rule enforcement hook). The Diátaxis companion makes correct fence choice easier; the enforcement hook catches incorrect fence choice when it manifests as drift. The two operate at different cognitive layers — methodology (this ADR) and enforcement (the hook ADR) — but together they close the "right content in right fence" loop.
