---
id: dec-draft-7b53c91c
title: context-engineer executes all interface-design artifact steps; main-agent handles plugin.json and diagram re-render
status: proposed
category: implementation
date: 2026-05-12
summary: Routes all context-artifact creation (skills, agent, rules, command, READMEs, consumer-agent wiring) to the context-engineer; main-agent retains two mechanical shell-toolchain steps.
tags: [implementation-planner, context-engineer, step-ordering, agent-coordination, interface-design]
made_by: agent
agent_type: implementation-planner
branch: worktree-interface-design
pipeline_tier: full
affected_files:
  - skills/web-ui-design/
  - skills/tui-design/
  - skills/agentic-interface-design/
  - skills/api-design-craft/
  - agents/interface-designer.md
  - agents/implementer.md
  - agents/verifier.md
  - agents/promethean.md
  - agents/implementation-planner.md
  - agents/systems-architect.md
  - commands/review-interface.md
  - agents/README.md
  - skills/README.md
  - commands/README.md
  - rules/swe/swe-agent-coordination-protocol.md
  - rules/swe/agent-model-routing.md
  - rules/swe/adr-conventions.md
  - rules/swe/agent-intermediate-documents.md
  - skills/software-planning/references/coordination-details.md
  - .claude-plugin/plugin.json
  - agents/diagrams/agent-pipeline-flowchart/src/agent-pipeline-flowchart.mmd
  - agents/diagrams/agent-pipeline-flowchart/rendered/agent-pipeline-flowchart.svg
---

## Context

The `interface-designer` capability involves 40+ artifact touch-points across 17 implementation steps: four new skill directories (each with ~7 reference files, SKILL.md, README), one agent file, three surgical edits to existing skills, four always-loaded rule additions + one non-always-loaded coordination-details section, five consumer-agent frontmatter edits, one slash command, three README updates, a Mermaid diagram restructure and re-render, and a `plugin.json` entry. The `swe-agent-coordination-protocol.md` rule states that for large-scope context work (3+ artifacts, restructuring, ecosystem-wide changes), the context-engineer executes the artifact steps. Two steps require shell toolchain invocation: `mmdc` for diagram re-rendering and direct JSON editing for `plugin.json` — which are mechanical, non-context-artifact operations.

## Decision

Route all context-artifact creation, editing, and wiring steps (Steps 1–9, 11–12, 14 of the implementation plan) to the **context-engineer** agent. The **main-agent (orchestrator)** retains exactly two mechanical steps: (Step 10) add the `interface-designer` entry to `.claude-plugin/plugin.json`, and (Step 13) edit and re-render the Mermaid diagram source with `mmdc`. No test-engineer is paired (all deliverables are Markdown; the verifier is the quality gate).

## Considered Options

**Option 1: Main-agent executes all steps directly.**
Rejected. The context-engineer has crafting-spec compliance authority for placement, conflict detection, and context-artifact correctness — the primary risk in a 40+ artifact ecosystem change. Bypassing it increases the probability of a misplaced reference, an over-broad rule addition, or a broken cross-reference.

**Option 2: Context-engineer executes all steps including plugin.json and diagram.**
Rejected for plugin.json (it is a JSON manifest, not a context artifact per the `agent-intermediate-documents.md` definition) and for diagram re-rendering (`mmdc` is a shell toolchain invocation, not a crafting decision). These two steps require shell access with no context-artifact judgment.

**Option 3: Multiple context-engineer instances dispatched concurrently per parallel group.**
Considered but not adopted. The sequential dependency chain (group B→C→D→E) means concurrent dispatch adds coordination overhead with no throughput gain in a single-worktree pipeline. The four group-B skills can be dispatched in parallel if multiple instances are available — this is left to the supervising main-agent's discretion at execution time.

**Option 4 (chosen): Context-engineer executes context-artifact steps (Steps 1–9, 11–12, 14); main-agent executes two mechanical steps (10, 13) and all verification steps (15–17).**

## Consequences

**Positive:**
- Context-engineer's crafting-spec validation is applied to all 40+ context artifacts, reducing misplacement and convention violations.
- Main-agent retains clear ownership of the two mechanical shell-toolchain steps and all verification runs.
- The split is coherent with the swe-agent-coordination-protocol.md "large-scope context work" rule.
- No test-engineer overhead — all Markdown artifacts; the verifier is the quality gate per the established pattern for artifact-creation pipelines.

**Negative:**
- Context-engineer executes Steps 1–9 sequentially; for group B (Steps 2–5) the four skills could be parallelized across multiple context-engineer instances at the supervising main-agent's discretion, but the plan does not mandate it (the dependency chain is the binding constraint regardless).
- The main-agent must checkpoint after each supervision point to catch context-engineer drift against the SYSTEMS_PLAN spec.
