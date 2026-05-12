---
id: dec-147
title: Dashboard validateProjectRoot requires only .ai-state/; missing PRAXION_PROJECT_ROOT renders an actionable error page
status: accepted
category: architectural
date: 2026-05-11
summary: Drop .ai-work/ from the required-directories check (it's gitignored and absent on fresh projects); treat its absence as "no active workshops". Add an error.tsx boundary + inline catch so a missing/invalid PRAXION_PROJECT_ROOT renders an actionable error UI, not a raw 500. No auto-creation of .ai-work/ (the dashboard is read-only).
tags: [dashboard, robustness, empty-state, error-ui, nextjs]
made_by: agent
agent_type: systems-architect
branch: worktree-dashboard-redesign
pipeline_tier: full
affected_files:
  - dashboard_app/src/server/artifacts/project-root.ts
  - dashboard_app/src/app/error.tsx
  - dashboard_app/src/lib/config.ts
---

## Context

`dashboard_app/src/server/artifacts/project-root.ts` has `REQUIRED_PROJECT_DIRECTORIES = [".ai-state", ".ai-work"]` — both must exist or `validateProjectRoot` throws "Invalid Praxion project root: missing required directories .ai-work". But `.ai-work/` is gitignored and only created when the first pipeline runs, so a freshly-onboarded project (only `.ai-state/`) makes every dashboard page throw a 500 on load — a direct violation of dashboard-conventions §6 ("Pages MUST NOT crash on absent files that are legitimately sparse or ephemeral"). Separately, every page component calls `getConfig()` which throws on a missing `PRAXION_PROJECT_ROOT` env var, producing a raw Next.js 500 with no user-facing guidance (the layout uses the safe `getShellConfig()` fallback, but pages don't).

Activation: borderline — it changes a documented invariant (the required-directories set) and adds an error surface. Recorded for the trail; small but load-bearing for first-use UX.

## Decision

1. `REQUIRED_PROJECT_DIRECTORIES = [".ai-state"]` — drop `.ai-work/`. The workshops view-model already returns `[]` when `.ai-work/` is absent (`listDirectoryByMtimeDesc` returns `[]` for a non-directory), so the workshops page already degrades to its empty state correctly — the only blocker was the up-front `validateProjectRoot` throw. **Do not** auto-create `.ai-work/` on startup: the dashboard is read-only over canonical project files (dashboard-conventions §1); creating a directory in the target project violates that.
2. Add `dashboard_app/src/app/error.tsx` — a route-segment error boundary rendering an `<ErrorState>` component with an actionable message ("`PRAXION_PROJECT_ROOT` is not set or is invalid — relaunch via `praxion-dashboard start <path>`, or export `PRAXION_PROJECT_ROOT=<abs-path>` and reload"). Pages keep calling `getConfig()`; the throw is caught by the boundary. Belt-and-suspenders: also wrap each page's `getConfig()` in a try/catch that renders `<ErrorState>` directly, so the message is identical whether the boundary or the inline catch fires.

## Considered Options

### A — Require only .ai-state/; .ai-work/ absence = "no active workshops" (chosen)

Pros: freshly-onboarded projects work; the workshops page already handles the empty case; no writes to the target project (read-only contract preserved). Cons: none material — strictly safer. Accepted.

### B — Auto-create .ai-work/ on startup

Pros: every page "just works". Cons: violates dashboard-conventions §1 (read-only — no secondary store, no shadow state, and certainly no directory creation in the target project). Rejected.

### C — Keep both required

Pros: status quo. Cons: every fresh project 500s; violates §6. Rejected.

## Consequences

**Positive:** Freshly-onboarded projects (only `.ai-state/`) render every page; a missing/invalid `PRAXION_PROJECT_ROOT` produces a helpful message, not a stack trace; dashboard-conventions §1 and §6 both stay PASS; no writes to the target project.

**Negative:** None material. A project with neither `.ai-state/` nor `.ai-work/` still errors — correct (it isn't a Praxion project); the error message says so and points at `praxion-dashboard install` / onboarding.

**Risks accepted:** None of note. The error-boundary message is generic enough to be project-agnostic (no Praxion-specific path baked in beyond the `praxion-dashboard` CLI name, which is part of the launcher contract).
