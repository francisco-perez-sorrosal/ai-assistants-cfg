---
id: dec-draft-af4e66ee
title: One `interface-designer` agent — advisory sub-architect with interface-layer decision authority, four skills as hats
status: proposed
category: architectural
date: 2026-05-12
summary: Add a single opus-tier `interface-designer` agent (a peer sub-architect for the interface layer, not subordinate to systems-architect) backed by four hat-skills; it designs and decides interface-layer technology, sketches UI/API designs, writes ADRs, but does not write production code.
tags: [architecture, agent, interface-design, pipeline, ui-ux, api-design]
made_by: agent
agent_type: systems-architect
branch: worktree-interface-design
pipeline_tier: full
affected_files:
  - agents/interface-designer.md
  - agents/implementer.md
  - agents/verifier.md
  - agents/promethean.md
  - agents/implementation-planner.md
  - .claude-plugin/plugin.json
  - agents/README.md
---

## Context

Praxion has deep system-architecture support (`systems-architect`) but no equivalent for the **interface layer** — the boundary where a system meets its consumers, human (web UIs, terminals/CLI) and machine (REST/GraphQL/gRPC APIs, MCP/agent tools, A2A). Two parallel research passes (`RESEARCH_FINDINGS_uxui.md`, `RESEARCH_FINDINGS_api.md`) distilled the durable design canon and flagged the encoding question as open: agent vs skills-only, one agent vs two, and — critically — what decision authority the capability should have. The user resolved these: one agent named `interface-designer`, opus tier, **advisory but holding design-decision authority within its domain** (it *makes* the interface-layer decisions — UI framework, API paradigm, MCP tool decomposition, error format, pagination, interaction model — not merely flags options for the architect to weigh), backed by four hat-skills, and it does **not** write production code (the `implementer` does, with the four skills injected).

## Decision

Add **one** agent, `agents/interface-designer.md`, at **opus** tier, structurally a clone of `context-engineer` (two operating modes — pipeline shadowing + standalone review; forward-only information flow; domain depth in injected skills rather than a bloated prompt; identical lifecycle plumbing — `permissionMode: acceptEdits`, `background: true`, `memory: user`, `maxTurns: 80`, the `send_event.py` Stop hook + `precompact_state.py` PreCompact hook). Its `skills:` frontmatter injects the four new hat-skills (`web-ui-design`, `tui-design`, `agentic-interface-design`, `api-design-craft`) plus `external-api-docs`. It is a **peer sub-architect for the interface layer** — a peer to `systems-architect`, not subordinate — that designs the interface architecture, decides the major interface-layer libraries/frameworks/paradigms, sketches the UI/UX and API/tool designs in text (ASCII/markdown mockups, state tables, resource models, endpoint shapes, tool JSON-schemas, error contracts), hands these forward as **authoritative inputs** the implementation-planner sequences and the implementer builds, and writes ADR fragments for its load-bearing calls. It does **not** write production code.

The four hat-skills are also selectively injected into pipeline consumers: `implementer` (builds the sketched designs), `verifier` (checks implementations against `INTERFACE_DESIGN.md` and the per-skill `design-review-checklist.md`), `promethean` (ideates user-facing/consumer-facing features). `doc-engineer` does **not** get them (it owns documentation quality, not design quality; the help-text overlap is served by `tui-design` being available to the implementer who writes the help text). `implementation-planner` does not get them injected (it reads `INTERFACE_DESIGN.md` as a document) but gets one prompt bullet noting it's an authoritative input to sequence.

## Considered Options

### Option 1 — No agent; four skills only, consumed by existing agents

The lighter option (matches the dec-014/dec-015 bare Skill+Command pattern). The `systems-architect` and `implementer` load the four skills directly.

- **Pro**: minimal coordination cost; no new agent in the roster; no new opus-tier agent.
- **Con**: interface-layer decisions (framework selection, API paradigm, MCP tool decomposition) are *trade-off-under-taste* decisions of the same character as the architect's — leaving them to a skill the architect/implementer reads means they get under-applied; the research itself flagged "what is the agent's decision boundary" as unresolved, and the user resolved it toward a *decision-making peer*, not a passive skill.

### Option 2 — Two agents (`web-ux-designer` + `api-designer`)

Split by surface family — human-facing vs machine-facing.

- **Pro**: each agent's prompt is narrower.
- **Con**: the four hats share the same canon (`design-fundamentals.md` is identical across all four) and the same two-mode structure; splitting duplicates the agent prompt and lifecycle plumbing for no separation benefit — the *skills* already provide context separation. Doubles the coordination cost.

### Option 3 (chosen) — One agent `interface-designer`, advisory-with-decision-authority, opus tier, four skills as hats

- **Pro**: a peer interface specialist whose decisions are authoritative; interface quality gets the same rigor as system architecture; the two-mode structure gives both proactive design and on-demand audit; the four-skill encoding keeps the prompt lean and the depth modular/reusable; structurally a clone of `context-engineer`, so the coordination model is already understood.
- **Con**: one more agent (incremental coordination cost), one more opus-tier agent (cost — but the agent only runs when an interface surface is in scope, and interface design is high-leverage).

## Consequences

**Positive:**
- The interface layer gets a peer sub-architect; the systems-architect's load is reduced (no longer needs to be an expert in UI frameworks, API paradigm trade-offs, and MCP tool decomposition).
- `INTERFACE_DESIGN.md` (pipeline mode) and the Interface Design Review (standalone mode) are well-defined handoff artifacts the planner/implementer/verifier consume.
- The four hat-skills are reusable beyond the agent (implementer/verifier/promethean get them; future projects get them via the plugin).
- Structurally identical to `context-engineer` — the coordination model, the shadowing semantics, the forward-only flow are all already understood and documented.

**Negative / accepted:**
- The advisory-with-authority model means the planner and implementer treat `INTERFACE_DESIGN.md` as binding within the interface lane — a wrong design is a wrong authoritative input; mitigated by the verifier checking implementations against it and by the standalone-review mode catching issues independently.
- The engagement trigger ("a task touches an interface surface") could over-fire — mitigated by scoping the trigger to *substantial* interface surfaces (a new web UI, a new TUI, a CLI-output pass, a new/changed API, an MCP tool surface), not "any task that prints a line".
- `doc-engineer` not getting the four skills means a doc-engineer reviewing CLI help-text docs consults `tui-design` by name rather than having it injected — accepted as a rare overlap served by the established by-name cross-reference pattern.

This decision pairs with `dec-draft-2fc1015c` (the opus-tier routing-rule row), `dec-draft-51aeea61` (the `interface-designer` ↔ `systems-architect` default partition), `dec-draft-46e9accc` (the active dynamic on top of that partition — the interface-designer's standing to challenge architectural decisions, the orchestrator-mediated loop), `dec-draft-3c309b4c` (the four-skill decomposition), and `dec-draft-49af87a8` (the `/review-interface` command). Each significant decision is also recorded in `LEARNINGS.md ### Decisions Made` by the implementation-planner.
