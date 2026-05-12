---
id: dec-draft-6c940795
title: Dashboard design system — globals.css CSS-custom-property token layer, single polished light theme, no icon dependency
status: proposed
category: architectural
date: 2026-05-11
summary: Formalize and extend the de-facto :root tokens into a real token layer (typography scale, spacing scale, radii, color tokens incl. status/grade colors, shadows) consumed by every component; add the missing chrome primitives (chip/badge, tabs, error state, popover, enhanced empty state); keep the warm-paper aesthetic; single light theme; inline-SVG icons only (no icon library); dark mode deferred.
tags: [dashboard, design-system, css, tokens, ux, nextjs]
made_by: agent
agent_type: systems-architect
branch: worktree-dashboard-redesign
pipeline_tier: full
affected_files:
  - dashboard_app/src/app/globals.css
  - dashboard_app/src/components/chrome/chip.tsx
  - dashboard_app/src/components/chrome/tabs.tsx
  - dashboard_app/src/components/chrome/error-state.tsx
  - dashboard_app/src/components/educational-popover.tsx
  - dashboard_app/src/components/empty-state.tsx
---

## Context

The redesign brief calls for a "full UX redesign — elegant, functional, educational, visually appealing — quality first" that is generic across all Praxion-managed projects. The current `dashboard_app/src/app/globals.css` already has *de-facto* tokens in `:root` (a warm-paper palette, three font stacks, a shadow), but components mix tokenized and ad-hoc values; there's no typography scale, no spacing scale, and several reusable chrome pieces are missing (the Streamlit reference had `artifact_card`, `educational`, `empty_state` widgets; the Next.js port has CSS classes and an `InfoHint`, not proper components). The scope question: how far does "full redesign" go — incremental polish, a token layer + chrome primitives, or full theming (dark + light) + an icon library + animations?

Activation: yes — establishes the visual contract everything else sits on.

## Decision

**Token layer + chrome primitives; single polished light theme; no icon set.** Formalize and extend the `:root` tokens: a typography scale (named roles or `--text-xs`..`--text-3xl`), a spacing scale (`--space-1`..`--space-8`), radii (`--radius-sm/md/lg`), color tokens (surface, surface-strong, text, muted, border, accent, accent-soft) plus **status colors** (`--status-accepted` / `--status-superseded` / `--status-proposed` / `--status-reaffirmation`) and **grade colors** (`--grade-a`..`--grade-d`) derived from the existing `good/warning/danger/info` family, and shadows. Every component reads tokens — no per-component hex values. Add the missing chrome primitives as React components: `Chip`/`Badge`, `Tabs`, `ErrorState`, `EducationalPopover` (replaces `InfoHint`), an enhanced `EmptyState` (adds an optional producer-path link), and `ArtifactCard` (replaces the duplicated `<article class="artifact-card">` pattern). Keep the warm-paper aesthetic — it's already pleasant — just make it consistent. **No icon library** (the ~5 icons needed — info "i", chevrons, reset, external-link, filter — are inline SVG, avoiding a dep + per-icon licensing). **No dark mode in v1** (the light theme is already polished; dark mode multiplies the CSS surface for unclear demand — deferred, tracked as tech debt). **No animation library** (CSS transitions only, as today). The visual ceiling is "a calm, professional documentation portal", not a flashy dashboard. The tokens carry no Praxion branding — a neutral, professional look usable by any project.

## Considered Options

### A — Incremental polish only (clean up CSS, no token layer)

Pros: least work. Cons: leaves the inconsistency (tokenized + ad-hoc values mixed); no single retune point; the status/grade colors the ADR graph + sparkline need would be scattered. Rejected — the brief says "full redesign", and a token layer is the foundation that makes the rest coherent.

### B — Token layer + chrome primitives + single light theme (chosen)

Pros: visual consistency; one place to retune; status/grade colors reusable by the new viz components; no new deps; the chrome primitives close the parity gap with the Streamlit widgets. Cons: dark mode deferred; inline-SVG icons only. Accepted.

### C — Full theming (dark + light) + icon library + animations

Pros: maximal polish. Cons: dark mode doubles the CSS surface (every token needs a dark value, every component needs verification) for unclear demand; an icon library adds a dep + licensing; animations add a lib + a maintenance surface — all speculative against a local read-only portal. Rejected for v1; dark mode tracked as tech debt.

## Consequences

**Positive:** Visual consistency across all surfaces; one retune point for the look; status/grade color tokens reused by `DecisionGraph` and `Sparkline`; the missing chrome primitives (`ArtifactCard`, enhanced `EmptyState`, `EducationalPopover`, `Chip`, `Tabs`, `ErrorState`) close the parity gap with the Streamlit reference; no new dependencies; the design tokens are project-agnostic.

**Negative:** Dark mode is deferred (logged as tech debt — owner-role: systems-architect); a polished icon set is replaced by ~5 inline SVGs; "full redesign" might be read by the user as also wanting dark mode / icons — flagged explicitly in SYSTEMS_PLAN so the user can object before decomposition.

**Risks accepted:** Refactoring every component to consume tokens touches a lot of CSS in one pass — mitigated by sequencing it as an early step (the token layer + the chrome primitives land before the page rewiring, so pages are written against the new tokens from the start). The `.metrics-summary-grid--sentrux` class and the `.info-hint*` classes are removed in this pass (coupled to Sentrux excision and the `EducationalPopover` introduction respectively).
