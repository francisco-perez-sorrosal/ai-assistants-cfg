---
id: dec-079
title: Model-routing policy lives in a new always-loaded rule
status: accepted
category: architectural
date: 2026-04-25
summary: The routing table + override rules live in a new always-loaded rule `rules/swe/agent-model-routing.md` — not path-scoped, not a skill, not in CLAUDE.md
tags: [model-routing, token-budget, rules, progressive-disclosure, always-loaded]
made_by: agent
agent_type: systems-architect
pipeline_tier: standard
affected_files:
  - rules/swe/agent-model-routing.md
  - rules/swe/swe-agent-coordination-protocol.md
  - skills/agent-crafting/references/configuration.md
affected_reqs:
  - AC1
---

## Context

The hybrid routing mechanism (dec-078) requires the main orchestrator to consult the tier table on every Agent-tool spawn. That means the policy content must reach the main session's loaded context — not only a subagent's prompt. At the same time, Praxion's always-loaded budget (CLAUDE.md files + unscoped rules) has a 25,000-token ceiling per dec-050, with ~15,100 currently used. The placement decision must balance visibility at spawn time against token-budget impact, while coexisting with two overlapping artifacts: `skills/claude-ecosystem/` (consumer-side model selection) and `skills/agent-crafting/` (authoring agents).

## Decision

Create `rules/swe/agent-model-routing.md` as an **always-loaded** rule (no `paths:` frontmatter). Keep the content compact (~800 tokens): 13-row agent→tier table + 4 principles + override section + operator runbook. Use aliases only (`opus`, `sonnet`, `haiku`). No model catalog; no benchmarks; no ADR numbers in-body.

Cross-reference from `rules/swe/swe-agent-coordination-protocol.md § Agent Selection Criteria` (one-line pointer). Add a floor-semantic note in `skills/agent-crafting/references/configuration.md` under the `model:` field entry.

## Considered Options

### Option 1 — Always-loaded rule (selected)

- Pros: Visible to the main orchestrator at spawn time (the right audience at the right moment). Declarative content maps to "rule" not "skill." Aligns with existing SWE rules (`adr-conventions.md`, `memory-protocol.md`) in shape and tone.
- Cons: ~800 tokens of always-loaded budget consumed. Mitigated by compact shape and ~9,100 tokens of headroom against the 25,000 ceiling.

### Option 2 — Path-scoped rule (`paths: [agents/**, skills/**, rules/**, ...]`)

- Pros: Zero always-loaded cost on non-agent-edit sessions.
- Cons: Invisible at spawn time — the main orchestrator is editing *code*, not agent definitions, when it spawns. Defeats the primary use case. Rejected.

### Option 3 — Skill `skills/agent-model-routing/`

- Pros: Progressive disclosure, zero always-loaded cost.
- Cons: Skills auto-activate from triggers in prose — the main orchestrator rarely types "route agent" in a way that a skill trigger would catch. Unreliable for the primary consumer. Rejected.

### Option 4 — Subsection of CLAUDE.md

- Pros: Always loaded at project scope.
- Cons: CLAUDE.md is for project identity and workflow, not domain policy. Would violate the separation embedded in Praxion's own rule/CLAUDE.md distinction. Rejected.

### Option 5 — Extend `swe-agent-coordination-protocol.md`

- Pros: Same always-loaded surface, no new file.
- Cons: That rule is already dense (~5,000 tokens) and owns agent coordination, not model selection. Mixing concerns weakens its focus. Cross-reference is cleaner. Rejected.

## Consequences

**Positive:**

- Main orchestrator always has the policy at hand. Zero guesswork at spawn time.
- Declarative rule form matches existing Praxion convention; no new artifact type.
- Aliases-only convention handles the 2026-06-15 Opus 4 / Sonnet 4 retirement transparently.

**Negative:**

- Adds ~800 tokens to always-loaded context. Budget headroom absorbs it; no other rule needs to shrink to compensate.

**Risks accepted:**

- Rule becomes stale as Anthropic ships new models. Mitigated by aliases-only (no staleness markers needed); rule review cadence implicit in the one-month telemetry revisit (dec-080).
- Context-engineer independently arrived at the same decision in `CONTEXT_REVIEW.md §F3`; concurrent validation of the placement choice.
