---
id: dec-draft-a0b3a823
title: architect-validator agent — pre-merge / on-demand structural validator for code↔DSL↔ADR coherence
status: re-affirmation
category: architectural
date: 2026-04-30
summary: 'Charter a new gated agent (model tier H/opus) that verifies the code↔DSL↔ADR triangle on architectural-touch slices, produces ARCHITECTURE_VALIDATION.md plus tech-debt-ledger rows on FAIL, runs in two modes (on-demand + pre-merge), and respects strict boundaries against verifier (behavior), doc-engineer (markdown), sentinel (periodic), cicd-engineer (harness).'
tags: [agent, architect-validator, aac, dac, validation, drift-detection, boundaries, model-routing]
made_by: agent
agent_type: systems-architect
pipeline_tier: standard
affected_files:
  - agents/architect-validator.md
  - rules/swe/swe-agent-coordination-protocol.md
  - rules/swe/agent-intermediate-documents.md
  - .claude-plugin/plugin.json
re_affirms: dec-draft-bbf06bcb
---

## Context

The promethean's Idea 4 charter named `architect-validator` as a planned-but-unscoped agent. Without a clear charter, its responsibilities will overlap with verifier (behavior), doc-engineer (markdown), sentinel (periodic), and cicd-engineer (CI harness), producing tooling-overlap debt. The agent must be defined precisely, with explicit inputs, outputs, modes, and boundary cells against each potentially-overlapping agent.

The fence contract (separate ADR) creates the convention surface; the architect-validator is the agent that reasons over it.

## Decision

Charter `architect-validator` as a **gated, pre-merge** (and **on-demand**) agent with one job: verify the **code↔DSL↔ADR triangle** is consistent before a PR can merge.

**Inputs:**

- LikeC4 DSL — preferred via the `likec4` MCP (already wired); fallback to direct `.c4` file reads when the MCP is unavailable.
- Code import graph — reuses `fitness/import-linter.cfg`'s resolved graph (the fitness-functions ADR establishes this).
- ADR set — reads `.ai-state/decisions/DECISIONS_INDEX.md` and individual ADR files for `affected_files` cross-references.
- Markdown fences — invokes `scripts/aac_fence_validator.py` (the fence-contract ADR establishes this script).

**Outputs:**

- `.ai-work/<task-slug>/ARCHITECTURE_VALIDATION.md` — three named sections (Model→Code drift, ADR→Model drift, Generated-region drift) with PASS/FAIL/WARN per finding and an overall verdict (PASS / PASS_WITH_WARNINGS / FAIL).
- TECH_DEBT_LEDGER row(s) on FAIL — `class: drift`, `goal-ref-type: architecture`, `owner-role: systems-architect`, `source: architect-validator`. This requires a one-line edit to `rules/swe/agent-intermediate-documents.md` adding `architect-validator` as a third writer alongside verifier and sentinel.

**Modes:**

- `--mode=on-demand` — slash command path. Always writes report; never blocks anything.
- `--mode=pre-merge` — CI gate path. Pre-merge mode triggers only on slices touching architectural paths (`docs/diagrams/**`, `**/*.c4`, `**/ARCHITECTURE.md`, `.ai-state/decisions/**`). On any FAIL finding, the supervising harness exits non-zero so CI can use it as a gate.

**Boundaries** (canonical table embedded in `rules/swe/swe-agent-coordination-protocol.md` per Decision 2 in the SYSTEMS_PLAN):

| Boundary | architect-validator does | The other agent does |
|----------|-------------------------|---------------------|
| vs **verifier** | Verifies code matches the architectural model (DSL, ADRs, fences) — **structure only** | Verifies code matches the acceptance criteria — **behavior only** |
| vs **doc-engineer** | Verifies DSL↔code↔ADR triangle coherence; reads markdown only inside `aac:generated` fences | Verifies markdown quality (broken links, prose drift) for non-generated regions |
| vs **sentinel** | Per-PR, slice-scoped, runs on architectural-touch paths only | Periodic, ecosystem-wide, runs across all artifacts |
| vs **cicd-engineer** | Performs structural reasoning; writes the verdict | Authors the GitHub Actions workflow that *invokes* the validator |

**Model tier:** `H/opus` per `agent-model-routing.md` — structural reasoning across DSL + code graph + ADR set is load-bearing and Opus-class.

**Frontmatter shape** (matches canonical agent template; see SYSTEMS_PLAN for full spec):

```yaml
name: architect-validator
description: <see SYSTEMS_PLAN>
tools: Read, Glob, Grep, Bash, Write
disallowedTools: Edit
model: opus
permissionMode: default
memory: user
maxTurns: 60
background: true
```

## Considered Options

### Option 1 — Single mode (pre-merge only)

**Pros:** Simplest agent surface; one entry point.

**Cons:** Cannot run on-demand during exploratory work; developers cannot validate locally without invoking CI. Forces the boundary "the validator only runs in CI" which couples it tightly to CI infrastructure.

### Option 2 — Two agents (one for pre-merge, one for on-demand)

**Pros:** Each agent has a single mode; no `--mode` flag needed.

**Cons:** Doubles the agent count for this capability. Two prompts to maintain; identical structural reasoning duplicated. Violates simplicity-first.

### Option 3 — One agent, two modes (chosen)

**Pros:** One agent, one prompt, one boundary specification. The mode flag is the only difference (always-write-report vs additionally-exit-non-zero-on-FAIL). Reuses the same Phase 1-7 process for both invocations. Smaller maintenance surface.

**Cons:** Mode-dependent exit behavior is a small piece of complexity in the supervising harness. Mitigated by making the harness convention explicit (one-line snippet in the agent prompt and the coordination protocol).

### Option 4 — Continuous (long-running, watches for changes)

**Pros:** Catches drift faster than gated cadence.

**Cons:** Massive cost overhead (Opus-class reasoning continuously running). Duplicates sentinel's role at much higher cost. Rejected; sentinel's periodic cadence (Idea 10 v1.1) is the right home for between-PR coverage.

## Consequences

**Positive:**

- Closes the enforcement gap between "model exists" and "model is true". Without this agent, model-centricity is aspirational.
- One agent, two clearly-scoped modes; small maintenance surface.
- Reuses existing infrastructure (`likec4` MCP, import-linter graph, ADR finalize protocol, fence validator).
- Explicit boundaries against four other agents — overlap risk minimized at design time.
- TECH_DEBT_LEDGER integration ensures unaddressed drift accumulates as tracked debt rather than evaporating with the ephemeral report.

**Negative:**

- Adds a new writer to TECH_DEBT_LEDGER.md (was: 2 writers — verifier, sentinel; now: 3 writers — + architect-validator). Requires a surgical rule edit; no rule restructuring.
- Pre-merge cadence misses drift introduced via non-architectural PRs (e.g., a refactor that violates a DSL constraint without touching `.c4` files). Covered by Idea 10's sentinel periodic run (deferred to v1.1).
- Agent invocation in pre-merge mode requires a supervising CI harness; v1 does not ship the harness (Idea 7 v1.1). v1 ships the agent fully runnable via slash command / Agent tool.

**Operational:**

- Plugin registration: add `agents/architect-validator.md` to the `agents` array in `.claude-plugin/plugin.json`.
- Coordination protocol update: add row to Available Agents table; add canonical boundary cells.
- Rule update: add `architect-validator` to `TECH_DEBT_LEDGER.md` Writers list with scope "per-PR drift findings, pre-merge or on-demand".
- The `dynamic` metadata tag in LikeC4 elements suppresses Model→Code drift findings on edges declared dynamic — handles plugin-loader patterns without false positives.
- When the LikeC4 MCP is unavailable in CI, the validator falls back to direct `.c4` reads and emits a single WARN about MCP unavailability.

## Prior Decision

This ADR depends on (re-affirms) `dec-draft-bbf06bcb` (the fence contract) — the validator's "Generated-region drift" section presupposes the fence schema. If the fence contract is later superseded with a different mechanism (e.g., sidecar files), the validator's Phase 3 input source changes; the boundary table and modes carry over.
