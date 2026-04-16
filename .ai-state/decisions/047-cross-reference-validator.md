---
id: dec-047
title: Cross-reference validator as sibling script with soft-launch CI
status: accepted
category: implementation
date: 2026-04-16
summary: New `skills/skill-crafting/scripts/validate_references.py` validates six link classes across skills/rules/agents/commands/docs/.ai-state/decisions; GitHub slugifier for anchors; stdlib-only; CI job `validate-context-artifacts` with 2-week `continue-on-error` soft-launch then strict
tags: [validation, ci, skills, link-check, tooling]
made_by: agent
agent_type: systems-architect
pipeline_tier: full
affected_files:
  - skills/skill-crafting/scripts/validate_references.py
  - skills/skill-crafting/SKILL.md
  - skills/skill-crafting/tests/test_validate_references.py
  - skills/skill-crafting/tests/fixtures/validate_references/
  - .github/workflows/test.yml
---

## Context

Cross-references between skills, rules, agents, commands, and ADRs are the main connective tissue of the ecosystem. Broken intra-repo links produce silent degradation — no error is raised until a reader clicks through. The existing `validate.py` covers frontmatter structure but not link targets. The ROADMAP and CONTEXT_REVIEW §4.4 propose a sibling validator script scoped to link validation. Scope decisions required: which files, which link classes, anchor-slug algorithm, output format, ignore mechanism, CI behavior during legacy cleanup.

## Decision

Create a new sibling script `skills/skill-crafting/scripts/validate_references.py` (confirming CONTEXT_REVIEW §4.4). Scope: all `.md` files across skills, rules, agents, commands, `docs/`, `.ai-state/decisions/`, and top-level `CLAUDE.md` / `README.md` / `ROADMAP.md`. Six link classes validated with per-class rules. CI integration via a new `validate-context-artifacts` GitHub Actions job with a 2-week soft-launch (`continue-on-error: true`), then strict.

**Link classes and rules:**

| Class | Example | Rule | Level |
|---|---|---|---|
| **Intra-skill relative** | `[x](references/y.md)` | File must exist relative to the SKILL.md directory | **FAIL** |
| **Sibling-skill relative** | `[x](../claude-ecosystem/SKILL.md)` | File must exist | **FAIL** |
| **Cross-artifact** | `[x](../../rules/swe/adr-conventions.md)` | File must exist | **FAIL** |
| **Anchor (same-file)** | `[x](#some-heading)` | Slug must match a heading in the same file | **FAIL** |
| **Anchor (cross-file)** | `[x](../claude-ecosystem/SKILL.md#gotchas)` | File must exist AND slug must match a heading in the destination | **FAIL** (both) |
| **External URL** | `https://docs.anthropic.com/...` | Skipped — do not network in CI | **OK** |
| **Code-file path** (link syntax) | `[file](memory-mcp/src/memory_mcp/schema.py)` | File must exist; match only if prefix matches repo-root allowlist | **FAIL** (when allowlisted) |
| **Code-file path** (bare backticks) | `memory-mcp/src/memory_mcp/schema.py` | Not validated (too many false positives) | **OK** |
| **Ambiguous slug collision** | Two headings producing same slug | Flag | **WARN** |
| **Path into ignored dir** (e.g., `.ai-work/`, `node_modules/`) | `[x](.ai-work/foo.md)` | Likely paste error | **WARN** |

**Repo-root allowlist for code-file link validation**: `memory-mcp/`, `task-chronograph-mcp/`, `hooks/`, `scripts/`, `skills/`, `agents/`, `rules/`, `commands/`, `.ai-state/`, `docs/`.

**Anchor slugification**: match GitHub's slugifier (primary rendering surface). Algorithm: lowercase → remove punctuation (except `-` and `_`) → replace spaces with `-` → strip leading/trailing `-` → on collision within a file, suffix `-1`, `-2` in document order. Implementation: port GitHub's logic; ~30 lines of Python with the `re` module.

**Scope: include**: `skills/*/SKILL.md`, `skills/*/README.md`, `skills/*/references/*.md`, `skills/*/contexts/*.md`, `rules/**/*.md`, `agents/*.md`, `commands/**/*.md`, `docs/**/*.md`, `.ai-state/decisions/*.md`, top-level `CLAUDE.md` / `README.md` / `ROADMAP.md` / `README_DEV.md`. **Exclude**: `.ai-work/**`, `**/node_modules/**`, `.venv/**`, `target/**`, `dist/**`, `build/**`, `memory-mcp/**/*.md`, `task-chronograph-mcp/**/*.md` (MCP server project docs with their own conventions).

**Output format**: dual mode via `--format={text,json}` (`text` default, human; `json` machine-readable for CI annotation). Exit codes: `0` = no FAILs (WARNs allowed), `1` = at least one FAIL, `2` = script error. Additional flags: `--warn-only`, `--strict`, `--all`, `--file <path>`.

**Ignore-list mechanism** (two-tier):

1. **Inline comment** (per-link): `[Example Link](path/to/thing.md) <!-- validate-references:ignore -->`
2. **File-level opt-out** (per-file): YAML frontmatter `validate-references: off`

Preferred mechanism: per-link inline comments. File-level reserved for template files whose entire purpose is to contain placeholder patterns.

**CI integration**: new job `validate-context-artifacts` in `.github/workflows/test.yml` with `continue-on-error: true` for the first 2 weeks (soft-launch), then a follow-up PR at day-14 removes that line flipping to strict.

## Considered Options

### Option 1 — Overload the existing `validate.py`

Rejected; frontmatter validation and link validation have different parsers (YAML vs full-markdown) and different failure modes; each should evolve independently.

### Option 2 — Use a third-party tool (`markdown-link-check`, `lychee`)

Rejected; these either require node/rust toolchains, network the external URLs, or have opinionated defaults that conflict with our allowlist model. A ~300-line Python script with stdlib + no deps is simpler to maintain.

### Option 3 — Validate external URLs via HEAD requests

Rejected; introduces CI flakiness (URLs go down or rate-limit), adds 30+ seconds to CI runtime, and doesn't protect against the actual failure mode (wrong link *path*, which a HEAD check can't diagnose).

### Option 4 — Sibling script + stdlib + soft-launch CI (chosen)

Scoped single-purpose tool; no dependencies; soft-launch cushions legacy cleanup without blocking PRs.

## Consequences

**Positive**: catches broken intra-repo links pre-merge (the biggest silent-degradation surface today). Minimal dependencies. Soft-launch cushion prevents spurious PR blocks during cleanup.

**Negative**: new CI job (~30s runtime); new script (~300 lines) to maintain. Initial legacy-cleanup burden (expected: 10–30 broken links lurking across skills/README/docs).

**Risk accepted**: GitHub slugifier behavior drifts between `.md` rendering engines; mismatches with e.g., Cursor's renderer are out of scope (we optimize for GitHub as the primary surface).
