---
id: dec-draft-95fc1a73
title: "Skill-genesis inversion: static-analysis test strategy for Markdown agent definitions"
status: proposed
category: implementation
date: "2026-05-15"
summary: "Tests for the skill-genesis inversion validate YAML frontmatter and grep patterns (static analysis), not runtime agent behavior — matching the testing approach used for other Markdown-based agent definitions in Praxion."
tags: [skill-genesis, testing, implementation, markdown-agents]
made_by: agent
agent_type: implementation-planner
branch: worktree-skill-genesis-pull-driven
pipeline_tier: standard
affected_files:
  - agents/skill-genesis.md
  - commands/skill-genesis.md
  - commands/skill-genesis-review.md
  - tests/test_skill_genesis_agent.py
  - tests/test_skill_genesis_review.py
re_affirms: dec-draft-1495b1f2
---

## Context

The skill-genesis pull-driven inversion produces three Markdown artifacts (one agent rewrite, two
new slash commands) as its primary deliverables. The pipeline's test-engineer must write behavioral
tests that validate the acceptance criteria before the implementer lands production code. The
question is: what kind of tests are appropriate for Markdown-defined agent and command files?

## Decision

Use **static analysis tests**: YAML frontmatter parsing, regex/grep for forbidden or required
patterns in the file body, and fixture-based schema validation for the report format. Do not
attempt runtime behavioral tests (e.g., launching Claude Code sessions or mocking agent execution).

## Considered Options

### Option 1: Static analysis tests (YAML parse + grep + fixture schema)

- **Pro**: Fast, deterministic, no external dependencies, no tool-call budget, runs in `pytest`
  without special infrastructure. Covers the exact ACs that are observable via file content.
- **Pro**: Consistent with existing Praxion test patterns — `tests/test_check_id_citation_discipline.py`
  and `tests/test_aac_fence_validator.py` both use static-analysis approaches over Markdown files.
- **Con**: Does not test runtime behavior (agent actually running, producing a report, etc.).
  Accepted — runtime testing requires a live Claude session and is out of scope for the `pytest` suite.

### Option 2: Runtime behavioral tests (invoke Claude session, check output files)

- **Pro**: Tests the full behavior end-to-end.
- **Con**: Requires `claude` CLI, a live model, credits, and non-deterministic execution time.
  Not feasible as a CI-gate `pytest` test. Out of scope.

### Option 3: Snapshot / golden-file tests

- **Pro**: Catches regressions in the full document text.
- **Con**: Brittle — any prose edit breaks the snapshot; over-specified for the AC coverage needed.
  The ACs are behavioral conditions (presence/absence of specific patterns), not full-text equality.

## Consequences

**Positive**:
- Tests run in milliseconds with no external dependencies.
- RED state on first run is deterministic: tests that grep for `background: true` in `agents/skill-genesis.md`
  fail predictably before Step 1 lands.
- The test suite can be run in CI alongside the existing Praxion tests without special setup.

**Negative**:
- No automated end-to-end validation that the agent actually produces a valid report at runtime.
  Mitigated by the verifier's manual review of the agent behavior and the self-review step (Step 8).
