---
id: dec-022
title: Extract coordination procedures to on-demand skill reference
status: accepted
category: architectural
date: 2026-04-11
summary: Move procedural detail from always-loaded coordination rules to a new on-demand `coordination-details.md` reference, preserving anchors for cross-references.
tags: [token-budget, progressive-disclosure, skills, rules, refactoring, coordination-protocol]
made_by: agent
agent_type: systems-architect
pipeline_tier: standard
affected_files:
  - rules/swe/swe-agent-coordination-protocol.md
  - rules/swe/agent-intermediate-documents.md
  - skills/software-planning/references/coordination-details.md
  - skills/software-planning/SKILL.md
  - claude/config/CLAUDE.md
---

## Context

Praxion's always-loaded content (CLAUDE.md files + rules without `paths:` frontmatter) must stay under a 15,000-token budget to preserve headroom for session work. Measured size at task start: ~16,785 tokens (~112% of budget), with the coordination protocol (~4,161 tokens) and intermediate documents rule (~2,753 tokens) together accounting for ~41% of always-loaded content. Sentinel report T02 (2026-03-16) warned the coordination protocol was approaching the ceiling and proposed extraction to the `agent-pipeline-details.md` reference as a mitigation path — that precedent exists but had not been extended to the remaining procedural detail.

The content mix in these rules is not uniform: some sections drive decisions in every session (tiers, available agents, proactive triggers, delegation checklists), while others describe step-by-step procedures consulted only when the procedure is about to run (worktree lifecycle, fragment-file merge, BDD/TDD paired-step execution, batched improvement 4-step procedure, shadowing activation). The latter category pays token cost on every session while delivering value only during specific pipeline moments.

## Decision

Extract procedural detail into a new `skills/software-planning/references/coordination-details.md` reference, paired with the existing `agent-pipeline-details.md`. Rules retain decision-driving content (tiers, agent inventory, triggers, checklists, principles) and are trimmed to summary-plus-pointer stubs for the extracted sections. Anchor IDs referenced by external documents are preserved on the slimmed rules to avoid breaking cross-references.

Specifically:
- Move from `swe-agent-coordination-protocol.md`: Pipeline Isolation step-by-step procedure, BDD/TDD execution detail, Batched improvement 4-step procedure, Context-engineer shadowing detail, Doc-engineer parallel execution detail, Task slug propagation long form
- Move from `agent-intermediate-documents.md`: Parallel Execution fragment-file table + merge procedure
- Preserve anchors: `#process-calibration`, `#pipeline-isolation`, `#parallel-execution`, `#task-slug-convention`
- Add `implementer` line to the condensed Standard/Full deliverables block in `claude/config/CLAUDE.md` (closes pre-existing inconsistency)
- Register the new reference in the `software-planning/SKILL.md` satellite files table

Projected net savings: ~1,370 tokens across the two rules, bringing always-loaded content well below the budget ceiling with a documented path to the <82% headroom target through follow-up phases.

## Considered Options

### Option 1: Single new reference file (`coordination-details.md`)

**Pros:**
- Clear conceptual boundary: `agent-pipeline-details.md` covers agent-centric reference material (boundaries, parallel rules, reconciliation); `coordination-details.md` covers pipeline-level coordination procedures (lifecycle, BDD/TDD, batched improvement)
- Preserves stability of existing reference — no reorganization, no new broken anchors
- Single file for consumers to read when looking for "how does a procedure work"

**Cons:**
- Adds a second reference file to maintain in the skill
- Weak boundary between the two references if future extractions blur the line

### Option 2: Append to existing `agent-pipeline-details.md`

**Pros:**
- No new file; avoids adding another satellite to the skill
- Single reference path for consumers

**Cons:**
- Inflates an already-large reference with procedural content it was not scoped for
- Mixes agent-centric material (what agents can/can't do) with pipeline-centric procedures (how to enter a worktree), harming readability and search
- Makes the file approach a size where it itself becomes a candidate for splitting — just pushes the problem

### Option 3: Multiple small references (`worktree-lifecycle.md`, `fragment-files.md`, ...)

**Pros:**
- Each file is focused and small

**Cons:**
- Proliferation of satellites (5+ references for the skill)
- Consumers must jump between files for related content (worktree entry and worktree exit cross-referenced across two files, fragment files and parallel execution cross-referenced across two files)
- Higher maintenance cost for each SKILL.md registration and cross-reference update

### Option 4: Aggressive extraction, including delegation checklists, to target <82% budget in one pass

**Pros:**
- Reaches original target in a single refactor
- Maximum token savings

**Cons:**
- Higher risk of degrading main-agent decision quality — delegation checklists drive prompt construction on every delegation, frequent enough that keeping them always-loaded is worthwhile
- Single-pass aggressive extraction prevents the learning loop (observe, iterate) that ecosystem health benefits from
- Exceeds the clear threshold of "content that describes a *procedure to run*" — delegation checklists describe *what to put in the prompt*, not *how to execute the prompt*

## Consequences

**Positive:**
- Always-loaded budget drops well below ceiling with headroom for growth (projected ~14,430 tokens of ~15,000 budget; further reductions available in phase 2)
- Lightweight and Direct tier sessions — the majority of work — never pay for the extracted procedural content
- Progressive disclosure pattern extended consistently (matches the existing `agent-pipeline-details.md` precedent)
- Cross-reference integrity preserved — no agent prompt or external link breaks
- Reader experience unchanged for pipeline execution: agents following pointers reach detailed content in a single read
- CLAUDE.md deliverables list is now consistent across all four main pipeline agents (systems-architect, implementation-planner, implementer, verifier)

**Negative:**
- One additional reference file in the `software-planning` skill to maintain
- Small "stub" sections in the slimmed rules (2-3 lines each) whose sole purpose is anchor stability — readable overhead, not a structural issue
- First pass does not reach the originally stated <82% budget target; a second phase (or path-scoping `coding-style.md`) is needed to hit that number. Documented explicitly in the systems plan

**Operational:**
- The refactor is pure content movement; no behavior change, no deployment, no runtime code affected
- `install_claude.sh` propagates the CLAUDE.md change to the user's `~/.claude/CLAUDE.md` on the next install
- Sentinel's T02 token budget check becomes the authoritative feedback loop for whether further extractions are needed
