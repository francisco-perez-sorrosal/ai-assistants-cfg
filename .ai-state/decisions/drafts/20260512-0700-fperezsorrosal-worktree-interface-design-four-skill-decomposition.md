---
id: dec-draft-3c309b4c
title: Four interface-design skills; `api-design-craft` is a new skill; cross-cutting fundamentals duplicated as `references/design-fundamentals.md` in each skill
status: proposed
category: architectural
date: 2026-05-12
summary: Encode interface-design domain knowledge as four hat-skills (web-ui-design, tui-design, agentic-interface-design, api-design-craft); api-design-craft is a new skill alongside api-design, not additive references; the shared canon lives as a canonical references/design-fundamentals.md duplicated verbatim across all four (deliberate duplication for separation-of-contexts).
tags: [architecture, skills, interface-design, ui-ux, api-design, progressive-disclosure, separation-of-contexts]
made_by: agent
agent_type: systems-architect
branch: worktree-interface-design
pipeline_tier: full
affected_files:
  - skills/web-ui-design/
  - skills/tui-design/
  - skills/agentic-interface-design/
  - skills/api-design-craft/
  - skills/api-design/SKILL.md
  - skills/mcp-crafting/SKILL.md
  - skills/agentic-sdks/SKILL.md
  - skills/README.md
---

## Context

The interface-designer agent (see `dec-draft-af4e66ee`) needs its domain knowledge encoded as skills — its "hats". The two research passes recommended: two UX skills (`web-ui-design` + `tui-design`) sharing a fundamentals reference, and a new `api-design-craft` skill alongside the existing `api-design` (which is a *methodology* skill — the API-first process, OpenAPI/GraphQL spec patterns, contract types). The research left open: where the cross-cutting fundamentals (Rams/Norman/Nielsen/Tufte/Bloch synthesis, the "interface = a contract" framing, the perception thresholds) should live, and whether `api-design-craft` should be a new skill or additive references inside `api-design`. Separation of contexts is a hard requirement — a web task must not pull in terminal rules; an agentic-tool task must not pull in WCAG ratios.

## Decision

**Four skills**, each its own directory with `SKILL.md` (≤500 lines, precise `description:` trigger) + `references/*.md` + `README.md`:

- `skills/web-ui-design/` — references: `design-fundamentals.md`, `visual-design-fundamentals.md`, `component-patterns.md`, `accessibility.md`, `motion-and-perceived-performance.md`, `design-review-checklist.md`.
- `skills/tui-design/` — references: `design-fundamentals.md`, `cli-output-and-ux.md`, `cli-ux-patterns.md`, `tui-frameworks.md` (led by Python `textual`/`rich` + Node `Ink`; Go's Charm/Bubble Tea as the quality exemplar), `terminal-accessibility.md`, `design-review-checklist.md`.
- `skills/agentic-interface-design/` — references: `design-fundamentals.md`, `tool-design-for-models.md`, `mcp-primitives-as-design-surfaces.md`, `agent-error-ergonomics.md`, `progressive-disclosure-of-tools.md`, `agent-contracts.md`, `design-review-checklist.md`.
- `skills/api-design-craft/` — references: `design-fundamentals.md`, `api-canon.md`, `rest-patterns.md`, `graphql-patterns.md`, `grpc-patterns.md`, `low-latency-ergonomics.md`, `design-review-checklist.md`.

`api-design-craft` is a **new skill** (not additive references in `api-design`). The surgical edits to `api-design` (RFC 9457 as the recommended error format; a one-line `api-design-craft` cross-reference bullet) are the *only* changes to it — additive, non-destabilizing.

**Three surgical edits** to existing skills accompany the four new skills:

1. **`skills/api-design/SKILL.md`** — in `### Standard Error Response`, replace the homegrown `{ error: { code, message, details, request_id } }` example with the RFC 9457 (Problem Details) shape (`type`, `title`, `status`, `detail`, `instance`, plus extension members); keep the surrounding prose and the anti-pattern row; add one `api-design-craft` cross-reference bullet to `## Integration with Other Skills`.
2. **`skills/mcp-crafting/SKILL.md`** — in the `### Tools — Executable Functions` subsection, after the tool examples, add one paragraph cross-referencing `agentic-interface-design` for tool-*design* quality (naming craft, description-as-interface, fat-vs-thin, progressive disclosure of tools, agent error ergonomics) — "this page covers *how to build* an MCP server; `agentic-interface-design` covers *how good* the tool design is."
3. **`skills/agentic-sdks/SKILL.md`** — in the `## Tool Integration Patterns` section (the staleness-tracked one), add one sentence pointing to `agentic-interface-design` for tool-*design* quality — the **reciprocal** of the cross-reference `agentic-interface-design`'s SKILL.md body carries pointing back to `agentic-sdks` for SDK-loop mechanics. Scope: `agentic-sdks` owns the SDK loop mechanics (wiring tools to the agent loop, framework selection, multi-agent orchestration); `agentic-interface-design` owns the tool-design craft (naming, description-as-interface, parameter disambiguation, error ergonomics, response-shape and token discipline for model consumption). This closes the "which skill do I load for tool design?" seam the context-engineer flagged (CONTEXT_REVIEW F2 / Rec-3). The single sentence does not remove or restructure any existing `agentic-sdks` content.

The cross-cutting fundamentals live as a **canonical `references/design-fundamentals.md` duplicated verbatim into each of the four skills' `references/` directories** (~150–200 lines: Rams 10 principles adapted for software; Norman's interaction vocabulary; Nielsen's 10 heuristics; Tufte's data-ink/chartjunk/small-multiples; the Bloch core; the laws of UX; the three perception thresholds + the 50ms input budget; Julie Zhuo's taste-before-craft; the canon roll-call with one durable lesson each; the "interface = the boundary where a system meets its consumer; design that boundary as a contract" framing). The interface-designer agent's prompt carries only the *one-paragraph north-star framing* (the framing sentence + the Rams/Norman/Nielsen/Tufte/Bloch/Zhuo roll-call in a single paragraph), pointing at `references/design-fundamentals.md` for the depth.

The four `design-fundamentals.md` copies must stay byte-identical (a `LEARNINGS.md` note records this invariant; each skill's README states "this reference is shared verbatim across the four interface-design skills"). Note: `dec-013` (layered-duplication-prevention) is the standing convention against content duplication — this is a *deliberate, documented exception* to it, justified by separation-of-contexts, not a violation; the exception is recorded here and in `LEARNINGS.md`.

## Considered Options

### `api-design-craft`: new skill vs additive `api-design` references

- **Additive references in `api-design`** — rejected: would bloat `api-design`'s activation footprint and blur "how to structure an API" (methodology) with "how good an API is" (taste) — two concerns that activate on different triggers; the research warns refactoring `api-design` risks destabilizing its existing consumers (`systems-architect`, `implementation-planner` already activate it); a *new* skill alongside is non-destabilizing and reusable beyond the interface-designer.
- **New skill `api-design-craft`** (chosen) — clean separation; reusable; non-destabilizing.

### Where the cross-cutting fundamentals live

- **In the agent's prompt only** — rejected: `implementer`/`verifier`/`promethean` also consume the skills and need the canon; the agent prompt isn't injected into them.
- **A fifth skill `interface-design-fundamentals` referenced by the other four** — rejected: a fundamentals-only skill has no concrete task trigger (unlikely to activate on its own), adds a fifth activation trigger, and a cross-reference from `web-ui-design` to `tui-design/references/...` would couple the web and terminal hats (a cross-reference to a fifth `interface-design-fundamentals` skill wouldn't couple them, but the fifth skill still doesn't earn its place per the pragmatism principle — it earns its place as a *reference file*, not a skill).
- **In each skill's `SKILL.md` body** — rejected: would balloon every SKILL.md past the 500-line guideline and put ~200 lines in four bodies (worse than four on-demand reference files).
- **A canonical `references/design-fundamentals.md` duplicated verbatim across the four** (chosen) — clean separation; each SKILL.md stays ≤500 lines; the canon is in one place to *edit* (update once, copy to four dirs); new hats add their own copy.

## Consequences

**Positive:**
- Clean separation of contexts — web task → only web content; terminal task → only terminal content; agentic task → no WCAG; API task → no terminal rendering.
- Each skill is independently reusable (implementer/verifier/promethean get them; future projects via the plugin).
- Each SKILL.md stays ≤500 lines; the depth is in on-demand reference files.
- New hats (a future `mobile-ui-design`, `voice-ui-design`) are added by creating a fifth skill with its own copy of `design-fundamentals.md` — no change to the existing four.
- `api-design` is left intact as a coherent methodology skill; the surgical edits to it are additive only.
- The three surgical edits (RFC 9457 in `api-design`; `agentic-interface-design` cross-ref in `mcp-crafting`; reciprocal `agentic-interface-design` cross-ref in `agentic-sdks`) close two cross-skill seams the context-engineer flagged — "which error format does an API use?" (F5: replace, don't add) and "which skill do I load for tool design?" (F2/Rec-3: bidirectional cross-ref between `agentic-sdks` and `agentic-interface-design`) — without restructuring any existing content.

**Negative / accepted:**
- `design-fundamentals.md` is physically duplicated four times (~600–800 lines total of duplicated canon). **The `sentinel`'s redundancy check will flag this** — it is *expected and intentional*, documented in `LEARNINGS.md`, in each skill's README, and here; the alternative (a fifth skill or cross-references) is worse for separation-of-contexts. A sync-check (sentinel rule or script) is a cheap follow-up if drift becomes real — flagged, not shipped (Praxion's flag-but-don't-ship-future-hardening pattern).
- Maintenance: updating the canon means updating four files — mitigated by it being durable, slow-moving content (Rams/Norman/Nielsen/Tufte/Bloch don't change).

This decision pairs with `dec-draft-af4e66ee` (the agent shape — these are its hats) and `dec-draft-51aeea61` (the architect boundary — these skills are what the interface-designer reads to make its decisions). Recorded in `LEARNINGS.md ### Decisions Made` by the implementation-planner.
