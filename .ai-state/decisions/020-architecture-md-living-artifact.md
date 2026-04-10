---
id: dec-020
title: Living ARCHITECTURE.md artifact in .ai-state/
status: superseded
superseded_by: dec-021
category: architectural
date: 2026-04-10
summary: Persistent architecture document maintained by pipeline agents via section ownership, stored in .ai-state/, following the SYSTEM_DEPLOYMENT.md precedent
tags: [architecture, documentation, ai-state, living-document, agent-pipeline]
made_by: agent
agent_type: systems-architect
pipeline_tier: standard
affected_files:
  - .ai-state/ARCHITECTURE.md
  - skills/software-planning/assets/ARCHITECTURE_TEMPLATE.md
  - skills/software-planning/references/architecture-documentation.md
  - agents/systems-architect.md
  - agents/implementation-planner.md
  - agents/implementer.md
  - agents/verifier.md
  - agents/sentinel.md
  - agents/researcher.md
  - agents/promethean.md
  - rules/swe/agent-intermediate-documents.md
  - rules/swe/swe-agent-coordination-protocol.md
  - skills/software-planning/SKILL.md
  - skills/software-planning/references/agent-pipeline-details.md
  - skills/doc-management/references/documentation-types.md
---

## Context

Praxion manages software systems that evolve over time. Architectural knowledge is currently fragmented across `docs/concepts.md` (static, manually authored), `README.md` (ecosystem overview), and 19 ADRs (decisions, not structure). There is no single document that captures WHAT the system IS -- its components, data flow, interfaces, dependencies, and constraints -- in a form that agents can read and maintain.

The SYSTEM_DEPLOYMENT.md precedent (dec-019) proved that living documents in `.ai-state/` work: template-driven creation, section ownership, four-layer staleness mitigation, and natural pipeline sequencing. The doc-engineer already scans for `ARCHITECTURE.md` files (line 59), and the doc-management skill defines architecture documentation conventions. The ecosystem is structurally ready for this addition.

Research findings (arxiv:2601.20404) show that structured project context with explicit file paths and component identifiers reduces agent time by 28.64% and tokens by 16.58%. An ARCHITECTURE.md optimized for machine-readability while remaining human-useful directly serves this finding.

The user's vision: "A breathing tree, ever mutating towards the sun of clarity, simplicity and cleanliness" -- the document should grow organically with the system, guided by fitness functions (sentinel audits) toward structural clarity.

## Decision

Introduce `.ai-state/ARCHITECTURE.md` as a persistent, living document maintained by pipeline agents through a section ownership model. The document has 8 sections (Overview, System Context, Components, Interfaces, Data Flow, Dependencies, Constraints, Decisions). Template and methodology reference live in `skills/software-planning/` (assets/ and references/ respectively).

Key design choices:
- **8 sections** (not 10, not 5): adds System Context, Interfaces, Dependencies to the doc-management 5-section base; drops Quality Attributes (merged into Constraints) and Evolution Notes (duplicates git history)
- **Software-planning skill placement**: ARCHITECTURE.md is a pipeline artifact created and maintained by planning agents, not a standalone documentation type
- **First Standard/Full pipeline as creation trigger**: deterministic, automatic, no complexity threshold judgment needed
- **Cross-reference (not subsumption) with SYSTEM_DEPLOYMENT.md**: each document has a clear identity -- structure vs operations
- **CLAUDE.md mention + on-demand reading for coordinator awareness**: zero token budget impact, progressive disclosure

## Considered Options

### Option 1: Living document in `.ai-state/` with software-planning skill (chosen)

**Pros:** Follows proven dec-019 recipe; agents that create/maintain it already load software-planning; no new skill needed; on-demand reading preserves token budget.

**Cons:** Conceptual distance between the two living documents (architecture in software-planning, deployment in deployment skill).

### Option 2: Separate `skills/architecture-documentation/` skill

**Pros:** Clean separation; dedicated activation.

**Cons:** Another skill to maintain (36th); activation surface overlaps with software-planning; rarely loaded independently.

### Option 3: Extend deployment skill to cover both documents

**Pros:** Single living document methodology location; proven patterns reused directly.

**Cons:** Semantically incorrect -- architecture is not deployment; confuses skill activation triggers.

### Option 4: Static architecture documentation (no living document pattern)

**Pros:** Simpler; no agent modifications needed.

**Cons:** Will drift (documented as the #1 anti-pattern in research); misses the evolutionary architecture insight that documentation should grow with the system.

## Consequences

**Positive:**
- Project architecture is documented persistently and maintained automatically by the pipeline
- Components, interfaces, data flow, and dependencies have a canonical, machine-readable location
- Sentinel and verifier can detect drift between documentation and actual code structure
- The AGENTS.md research-backed 28.64% efficiency gain becomes achievable for Praxion-managed projects
- Completes the documentation triad: ADRs (why) + ARCHITECTURE.md (what) + SYSTEM_DEPLOYMENT.md (how)

**Negative:**
- Seven agent definitions need small modifications (~2-15 lines each)
- Sentinel definition grows from 463 to ~478 lines (approaching 500-line ceiling)
- Staleness risk exists despite four-layer defense
- Two rules and two skills need updates (small, well-scoped changes)

## Prior Decision

This decision extends the living document pattern established by dec-019 (SYSTEM_DEPLOYMENT.md). The six-element recipe (template, methodology reference, section ownership, staleness mitigation, pipeline sequencing, reconciliation entry) is reused with domain-appropriate adaptations. Dec-019 is not superseded -- both living documents coexist with cross-references.
