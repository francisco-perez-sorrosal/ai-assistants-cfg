---
id: dec-146
title: Dashboard renderer registry + Diátaxis-typed shells (Next.js App Router shape)
status: accepted
category: architectural
date: 2026-05-11
summary: Introduce a lightweight typed Map<diataxis|contentType, ReactComponent> renderer registry that the documentation page dispatches through; build reference + explanation + default shells, stub the other three Diátaxis types. This is the contract the html-output-conventions.md rewrite describes — replacing the phantom Python-shaped dashboard_app/components/ structure.
tags: [dashboard, renderer-registry, diataxis, nextjs, html-output-conventions]
made_by: agent
agent_type: systems-architect
branch: worktree-dashboard-redesign
pipeline_tier: full
affected_files:
  - dashboard_app/src/components/registry.ts
  - dashboard_app/src/components/shells/reference.tsx
  - dashboard_app/src/components/shells/explanation.tsx
  - dashboard_app/src/components/shells/default.tsx
  - dashboard_app/src/app/documentation/page.tsx
  - rules/writing/html-output-conventions.md
---

## Context

`rules/writing/html-output-conventions.md` prescribes a `dashboard_app/components/` directory with `render(source_paths, ...)` callables and an `__init__.ts` registry — a Python-influenced structure that does not map to Next.js App Router (and would collide with the actual `dashboard_app/src/components/`). The colleague who ported the dashboard built idiomatic Next.js instead: `src/server/view-models/` (data shaping) + `src/components/` (presentation primitives) + `src/app/<surface>/page.tsx` (composition), with no `render()` callable, no `__init__.ts`. The rule also references phantom sentinel checks (`EC07-doc-manifest-fresh`, `EC07b`). Meanwhile the Diátaxis-typed shells the rule describes (`tutorial`/`how-to`/`reference`/`explanation`/`concepts`) don't exist — the documentation page uses generic `MarkdownSurface` for everything regardless of `diataxis:` frontmatter. The CONTEXT_REVIEW asked the architect to settle: formal renderer registry, or direct page-level composition (and rewrite the rule to match whichever)?

Activation: yes — settles the component/renderer model that the rule rewrite depends on.

## Decision

Introduce a **lightweight typed registry**, not the Python-shaped one. `dashboard_app/src/components/registry.ts` exports `RENDERER_REGISTRY: Map<string, React.ComponentType<{ body: string; surface?: ManifestSurface }>>` (keys: `diataxis:` values `"tutorial" | "how-to" | "reference" | "explanation" | "concepts"` plus content-type strings like `"markdown"`) and `resolveRenderer(diataxis?, contentType?)` → diataxis-match → content-type-match → `DefaultShell`. Shells live in `dashboard_app/src/components/shells/`. The **documentation page** dispatches through the registry for v1 (it's the page with genuinely heterogeneous frontmatter-typed content); other pages stay as direct compositions — the registry is *available* to them, not mandatory.

Build **`ReferenceShell`** (fixed ToC sidebar slot from the markdown's headings + dense-table styling), **`ExplanationShell`** (wide prose column + "why this matters" aside slot), and **`DefaultShell`** (plain card). Register `tutorial` / `how-to` / `concepts` as default-aliasing stubs (`export { DefaultShell as TutorialShell }` etc.) — the registry entry exists, the chrome is the default chrome, until someone builds dedicated shells (tracked as tech debt). All shells are pure layout wrapping `<MarkdownSurface>` — zero project-specific content.

The crisp contract handed to the context-engineer for the `html-output-conventions.md` rewrite: *server view-models in `dashboard_app/src/server/view-models/`; presentation primitives in `dashboard_app/src/components/`; Diátaxis shells in `dashboard_app/src/components/shells/`; the `RENDERER_REGISTRY` Map at `dashboard_app/src/components/registry.ts` with `resolveRenderer(diataxis?, contentType?)`; page routes in `dashboard_app/src/app/<surface>/page.tsx`; the documentation page dispatches through the registry. There is no `render(source_paths)` callable, no `__init__.ts`, no flat `dashboard_app/components/` directory. No `EC07-doc-manifest-fresh` / `EC07b` checks (they were never implemented; if a manifest-freshness check is wanted later it gets a new ID, never reusing `EC07`).*

## Considered Options

### A — Keep direct page-level composition; rewrite the rule to describe exactly that (no registry)

Pros: simplest; nothing new. Cons: throws away the rule's *intent* (a renderer registry keyed by content type + Diátaxis); no extension point for new content-typed surfaces; the documentation page keeps ignoring `diataxis:`. Rejected — the intent is sound, only the Python shape is wrong.

### B — Lightweight typed registry, one consumer in v1 (chosen)

Pros: a real extension point matching the rule's intent; minimal (a `Map` + a resolver, ≈ 30 LOC); pages that don't need it ignore it; the documentation page finally honors `diataxis:`. Cons: a tiny indirection on one page; one more concept (mitigated by the rule rewrite documenting it crisply). Accepted.

### C — Full Python-shaped registry (`render(source_paths)` callables, `__init__.ts`)

Pros: matches the rule as written. Cons: doesn't fit Next.js; the colleague already built the idiomatic structure; forcing this would be a rewrite-for-the-rule's-sake. Rejected — fix the rule, not the code.

## Consequences

**Positive:** The rule rewrite has a concrete, idiomatic-Next.js contract to describe; the documentation page honors `diataxis:`; `reference` and `explanation` surfaces (the bulk of Praxion's `docs/`) get real layout chrome; the registry is a clean extension point for the deferred per-artifact renderers (metrics-JSON / plan / verification-report / idea-grid surfaces).

**Negative:** `tutorial` / `how-to` / `concepts` surfaces render in default chrome until dedicated shells are built (tech debt logged); the registry has exactly one consumer in v1 (deliberate — avoids speculative generality; deleting it if useless is a ~30-line revert).

**Risks accepted:** Over-engineering — countered by the one-consumer scope; the rule rewrite is downstream of code that's still being written, so the *contract above* (not the not-yet-final code) is the spec the context-engineer rewrites against — an implementer deviation from the contract is an objection-register moment, not silent rule/code drift.
