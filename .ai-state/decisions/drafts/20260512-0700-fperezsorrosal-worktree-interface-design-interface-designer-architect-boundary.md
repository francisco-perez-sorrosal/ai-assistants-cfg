---
id: dec-draft-51aeea61
title: The `interface-designer` ↔ `systems-architect` boundary — the default partition (interface-layer technology selection moves to `interface-designer`)
status: proposed
category: architectural
date: 2026-05-12
summary: The DEFAULT PARTITION — systems-architect decides THAT an interface surface exists and its role in the system; interface-designer decides WHAT it looks like — the resource/endpoint/tool model, error contract, pagination strategy, UI framework, component patterns, design tokens, interaction model. The two coexist as concurrent shadows. agents/systems-architect.md gets additive bullets; no change to onboarding modes. On top of this partition, dec-draft-46e9accc adds the active dynamic — the interface-designer is a quality advocate with standing to challenge architectural decisions that constrain a materially-better design, via an orchestrator-mediated loop.
tags: [architecture, agent, interface-design, pipeline, boundary, systems-architect, technology-selection]
made_by: agent
agent_type: systems-architect
branch: worktree-interface-design
pipeline_tier: full
affected_files:
  - agents/systems-architect.md
  - agents/interface-designer.md
  - rules/swe/swe-agent-coordination-protocol.md
---

## Context

`systems-architect` today does technology selection broadly. Introducing `interface-designer` (see `dec-draft-af4e66ee`) as a peer sub-architect for the interface layer requires drawing a clean boundary between the two — otherwise both agents claim the same decisions. The user's framing: `systems-architect` decides *that* there is an API / a dashboard / a CLI surface / an MCP server and its *role* in the system; `interface-designer` decides *what it looks like*. The boundary must also not break `systems-architect`'s two onboarding modes (`baseline-audit` mode for `/onboard-project` Phase 8 — produces `.ai-state/DESIGN.md` + `docs/architecture.md` from a structural read with no feature scope; full-feature-scope mode for greenfield `/new-project`) per the note in `agents/CLAUDE.md`.

## Decision

This ADR defines the **default partition** of decision authority between the two agents. The *active dynamic* layered on top of it — the interface-designer's standing to challenge architectural decisions that constrain a materially-better design, the architect's obligation to re-evaluate a substantive challenge, the orchestrator-mediated loop-back, and the user-escalation path on non-convergence — is `dec-draft-46e9accc` ("Specialist sub-architects are active quality advocates with standing"). Read the two together: this ADR is the *who-owns-what* baseline; `dec-draft-46e9accc` is *what happens when the baseline produces a suboptimal interface*.

Carve out the **interface layer** (the default partition):

- `systems-architect` decides **that** there is an API / a dashboard / a CLI surface / an MCP server and its **role** in the system — what subsystem owns it, how it fits the data flow, what it must do behaviorally, the deployment topology implications. System-level technology selection (database, message broker, language, deployment target, *whether* an interface surface exists and its role) stays with `systems-architect`.
- `interface-designer` decides **what it looks like** — the resource/endpoint/tool model, the error contract (RFC 9457), the pagination strategy (cursor vs offset), the UI framework (Radix/Tailwind/shadcn for web, `textual`/`rich` for Python TUIs, `Ink` for Node TUIs), the component patterns, the design tokens, the interaction model, the help-text structure, the exit codes. Interface-*layer* technology selection moves from `systems-architect` to `interface-designer`.

Tiebreaker rule for the ambiguity zone (e.g., SSR vs SPA): **if it changes the data flow / deployment topology, it's the architect's; if it changes only what the consumer sees and interacts with, it's the designer's.**

The two agents **coexist as concurrent shadows** — the architect cannot spawn the designer (agents cannot spawn agents); the main agent spawns both in parallel when an interface surface is in scope, exactly as it spawns `context-engineer` when context artifacts are in scope. Handoff via shared documents: the architect's `RESEARCH_FINDINGS*.md` + `SYSTEMS_PLAN.md` (which says *that* an interface exists and its role) → the designer's `INTERFACE_DESIGN.md` (the authoritative interface architecture + framework decisions + UI/UX + API/tool sketches) + ADR fragments → the architect, if still running, cross-references `INTERFACE_DESIGN.md` from `SYSTEMS_PLAN.md`'s Interfaces section rather than re-deriving it. Information flows **forward only** — the architect reads the designer's `## Research Stage` section if present when scoping the interface's role; if not present yet, the architect scopes conservatively and the designer's `## Architecture Stage` section refines within that scope.

`agents/systems-architect.md` gets an **additive "With the Interface Designer" bullet** in its Collaboration Points section — stating the default partition above, noting that when an interface surface is in scope the interface-designer shadows this stage and produces `INTERFACE_DESIGN.md` (the architect reads its research-stage section when scoping the interface's role and cross-references its output rather than re-deriving interface details), **and** stating the architect's `dec-draft-46e9accc` obligation: when the interface-designer registers a substantive challenge in `INTERFACE_DESIGN.md`'s `## Architecture Challenges` section and the orchestrator routes it back, the architect must re-evaluate — engage with the proposed alternative and its quality rationale, then accept or reject with a reason; it may not dismiss it. **No change** to either onboarding mode's anti-instructions — neither mode invokes the interface-designer: `baseline-audit` describes what *is* (no design decisions), and the greenfield seed pipeline is deliberately minimal and makes any interface decisions with the four skills available rather than by spawning a separate agent. `agents/CLAUDE.md`'s onboarding-hook note already covers this; the implementer confirms it needs no change.

## Considered Options

### Option 1 — `systems-architect` keeps all technology selection; `interface-designer` only advises

Rejected — the user explicitly wants the designer to *decide*; advice-only is the lighter model the user overrode (see `dec-draft-af4e66ee`).

### Option 2 — `interface-designer` owns all interface-related decisions including *whether* there is an API/dashboard/CLI

Rejected — deciding *that* there is an API and its role in the system affects the data flow, the deployment topology, the subsystem boundaries — that belongs with `systems-architect`.

### Option 3 (chosen) — Carve out the interface layer: architect decides *that* + *role*, designer decides *what it looks like*

The two coexist as concurrent shadows; the architect doc change is one additive bullet; no onboarding-mode change.

- **Pro**: a clear, defensible boundary that maps onto the existing `context-engineer` shadow model — incremental coordination cost, not novel; the architect's load is reduced; the architect doc change is surgical, preserving both onboarding modes.
- **Con**: a small ambiguity zone (resolved by the data-flow/deployment-topology tiebreaker, documented with examples); the two agents running concurrently means the architect might scope the interface's role before reading the designer's research-stage section — accepted because information flows forward (exactly like `context-engineer`).

## Consequences

**Positive:**
- Clear boundary — system role vs interface appearance — mapping onto the existing `context-engineer` shadow model, so coordination cost is incremental.
- Interface decisions get a specialist; the architect no longer has to be an expert in UI frameworks, API paradigm trade-offs, and MCP tool decomposition.
- The `agents/systems-architect.md` edit is surgical (one bullet); both onboarding modes preserved.

**Negative / accepted:**
- A small ambiguity zone — resolved by the data-flow/deployment-topology tiebreaker, documented in the boundary section with examples.
- Concurrent execution means the architect might scope the interface's role before reading the designer's research-stage section — accepted; forward-only flow handles it.
- If a future change to `/onboard-project` or `/new-project` *does* want interface-designer involvement, the "neither onboarding mode invokes interface-designer" statement would need revisiting — flagged in the boundary section as a known scope boundary.

This decision pairs with `dec-draft-af4e66ee` (the agent shape), `dec-draft-3c309b4c` (the four hat-skills the designer reads to make its decisions), and `dec-draft-46e9accc` (the active dynamic layered on this default partition — the standing-to-challenge, the architect's obligation-to-re-evaluate, the orchestrator-mediated loop, the user-escalation path). Recorded in `LEARNINGS.md ### Decisions Made` by the implementation-planner.
