---
diataxis: reference
audience: developer
---

# Rules Taxonomy and Blacklist Guide

Every Praxion-onboarded project inherits a curated set of always-loaded rules: coding style, behavioral contract, agent coordination protocol, ADR conventions, and more. These rules cost tokens on every session. This guide explains how rules are categorized, which ones you can disable, and how to measure the cost of your choices.

## Two-Channel Delivery

Praxion delivers rules through two channels to balance consistency with flexibility:

| Channel | Rules | Delivery | Disableable | Use case |
|---------|-------|----------|-------------|----------|
| **Symlinked** | 5 core + 14 path-scoped | Installed to `~/.claude/rules/` | No | Non-negotiable behavioral invariants + optional-depth guides |
| **Hook-injected** | 3 blacklistable | Injected at SessionStart via `additionalContext` | Yes | Project-specific conventions (agent lifecycle, memory, commit format) |

Core rules are always present. Path-scoped rules are loaded only when you read or edit files matching their patterns — they cost zero tokens until triggered. Blacklistable rules are always-loaded by default, but you can disable them per-project via `.claude/praxion-rules.yaml`.

## Three Rule Categories

### 1. Core Rules (non-disableable, always-loaded)

Five rules encode Praxion's behavioral contract and coordination protocol. They are **never disableable** — attempting to disable one produces a warning and the rule remains loaded.

| ID | Rule file | Purpose | Token cost |
|----|-----------|---------|------------|
| `CLAUDE` | `rules/CLAUDE.md` | Agent reading order + build/test/lint + repo layout | ~640 tokens |
| `swe/adr-conventions` | `rules/swe/adr-conventions.md` | Architecture Decision Record format, lifecycle, finalize protocol | ~3115 tokens |
| `swe/agent-behavioral-contract` | `rules/swe/agent-behavioral-contract.md` | Four non-negotiable behaviors: Surface Assumptions, Register Objection, Stay Surgical, Simplicity First | ~375 tokens |
| `swe/agent-intermediate-documents` | `rules/swe/agent-intermediate-documents.md` | `.ai-work/` and `.ai-state/` document locations, lifetimes, task-slug convention | ~3200 tokens |
| `swe/swe-agent-coordination-protocol` | `rules/swe/swe-agent-coordination-protocol.md` | Agent pipeline, tier table, delegation checklists, parallel execution | ~4245 tokens |

**Total core tokens:** ~11,575

### 2. Blacklistable Always-Loaded Rules (disableable)

Three rules are always-loaded by default but can be disabled per-project if your team follows different conventions.

| ID | Rule file | Purpose | Token cost | Typical disabler |
|----|-----------|---------|------------|------------------|
| `swe/memory-protocol` | `rules/swe/memory-protocol.md` | Memory MCP usage, recall, remember, conflict resolution | ~1248 tokens | Projects with memory-mcp disabled |
| `swe/agent-model-routing` | `rules/swe/agent-model-routing.md` | Claude model tier routing table, per-agent allocation | ~1619 tokens | Projects with custom model strategy |
| `swe/vcs/git-conventions` | `rules/swe/vcs/git-conventions.md` | Commit scope, message format, secrets discipline | ~2180 tokens | Projects with different VCS policy or no Git |

**Total blacklistable tokens:** ~5,047

### 3. Path-Scoped Rules (optional-depth, zero cost until triggered)

Fourteen rules load only when you read or edit files matching their patterns. They cost zero tokens until then, so they don't appear in the blacklist mechanism.

| Category | Rule ID(s) | Activation pattern | Purpose |
|----------|------------|-------------------|---------|
| **SWE** | `swe/coding-style` | `.py`, `.ts`, `.rs`, `.go` | Language-specific code formatting |
| | `swe/id-citation-discipline` | Spec files, implementation docs | REQ-to-code traceability conventions |
| | `swe/shipped-artifact-isolation` | Rules, skills, commands, agents | Constraints on project-portable artifacts |
| | `swe/staleness-policy` | `.md` files | Documentation freshness conventions |
| | `swe/testing-conventions` | Test code, specs | Testing strategy and terminology |
| | `swe/vcs/pr-conventions` | `.github/`, PR-adjacent surfaces | Pull request workflow and merge policy |
| **ML/AI** | `ml/eval-driven-verification` | Training plans with metric thresholds | ML eval-driven acceptance criteria |
| | `ml/experiment-tracking-conventions` | `program.md`, experiment tracking | Experiment tracking tool conventions |
| | `ml/gpu-budget-conventions` | Training steps, WIP.md | GPU compute budget enforcement |
| **Writing** | `writing/aac-dac-conventions` | `ARCHITECTURE.md` | Architecture-as-Code fence conventions |
| | `writing/diagram-conventions` | Diagram source files, rendered SVGs | Diagram toolchain and layout rules |
| | `writing/html-output-conventions` | `.html` files | HTML output generation |
| | `writing/readme-style` | `README.md`, documentation | Markdown writing quality and structure |

## Creating a Project Blacklist

### Step 1: Create `.claude/praxion-rules.yaml`

Create a YAML file in your project root (committed to git) specifying which blacklistable rules to suppress:

```yaml
# .claude/praxion-rules.yaml — Project-local rule configuration
# 
# Optional file. If absent, all rules load (backward compatible).
# Schema version 1 only (non-negotiable).

version: 1

# Disable specific rules by ID
disable:
  - swe/memory-protocol  # Our team uses cloud storage, not memory MCP

# Or disable all rules in a category with globs
# disable:
#   - ml/*                # This project is not ML-focused
#   - writing/*           # We use a different documentation standard
```

### Step 2: Understand the Behavior

- **No config file** → all rules load (no change from today)
- **Empty `disable` list** → all rules load
- **`disable: [swe/memory-protocol]`** → load core rules + other blacklistable rules, skip memory-protocol
- **`disable: [ml/*]`** → disable all ML rules in one entry (glob support)
- **Attempting `disable: [swe/agent-behavioral-contract]`** → warning emitted, rule stays loaded (core protection)

### Step 3: Measure the Effect

Use `measure_context_surface.py` to see the token delta:

```bash
# Baseline (all rules)
python3 measure_context_surface.py

# After adding a blacklist
python3 measure_context_surface.py
```

The tool reports always-loaded token totals before and after your configuration change.

## Category Globs

The disable list supports glob patterns for categories:

| Glob | Matches |
|------|---------|
| `ml/*` | All three ML rules: `ml/eval-driven-verification`, `ml/experiment-tracking-conventions`, `ml/gpu-budget-conventions` |
| `writing/*` | All four writing rules: `writing/aac-dac-conventions`, `writing/diagram-conventions`, `writing/html-output-conventions`, `writing/readme-style` |
| `swe/vcs/*` | Both VCS rules: `swe/vcs/git-conventions`, `swe/vcs/pr-conventions` (note: `vcs/pr-conventions` is path-scoped, not disableable) |
| `swe/*` | All SWE rules in the category (only `swe/memory-protocol` and `swe/agent-model-routing` are disableable; core rules are protected) |

## Core Rule Protection

If you attempt to disable a core rule, the SessionStart hook emits a warning to stderr:

```
[inject_rules] WARNING: rule swe/agent-behavioral-contract is core and cannot be disabled
```

The rule remains loaded. Core rules protect Praxion's behavioral contract (Surface Assumptions, Register Objection, Stay Surgical, Simplicity First) and are non-negotiable.

## Schema Version Handling

The `.claude/praxion-rules.yaml` format uses semantic versioning. The current schema is **version 1**.

- **Schema 1** (current): rules identified by `id`, glob support, `disable` list, no enable-list
- **Schema 2+**: not yet released

If your config specifies `version: 2` or higher:
- The hook emits an error: `schema version N is not supported; using schema 1 behavior`
- The hook falls back to injecting all blacklistable rules (fail-open)
- Update your `.claude/praxion-rules.yaml` to `version: 1` and remove any unsupported fields

## Kill Switch: Disable Rule Injection Entirely

For debugging or temporary disabling of all Praxion rule injection (including core and blacklistable rules delivered via hook), set the environment variable:

```bash
PRAXION_DISABLE_RULE_INJECTION=1 claude-code
```

This disables the `inject_rules.py` hook entirely for that session. Core rules symlinked into `~/.claude/rules/` are still loaded by Claude Code's native mechanism; only the hook-delivered blacklistable rules are suppressed.

**Use case:** Troubleshooting rule interaction issues without uninstalling the plugin.

## Verification and Measurement

### `measure_context_surface.py` — Token Accounting

After configuring a blacklist, measure the impact:

```bash
python3 measure_context_surface.py
```

This script:
1. Counts characters in your project's always-loaded CLAUDE.md files
2. Counts characters in core + non-blacklisted rules
3. Applies a conservative character→token ratio (÷3.6)
4. Reports the total always-loaded token budget

**Expected output:**
```
Always-loaded token budget:
  CLAUDE.md files:      2,000 tokens
  Core rules:          11,575 tokens
  Blacklistable rules:  3,000 tokens (2 of 3 enabled)
  Total:               16,575 tokens
```

If you disable `swe/memory-protocol` (~1,248 tokens), the total drops to ~15,327 tokens.

### SessionStart Logging

When a session starts, the `inject_rules.py` hook logs a summary line to stderr:

```
[inject_rules] Loaded 5 core rules; injected 3/3 blacklistable rules (suppressed: none)
```

or

```
[inject_rules] Loaded 5 core rules; injected 2/3 blacklistable rules (suppressed: swe/memory-protocol)
```

This line confirms which rules were loaded and which were suppressed for that session.

## Example Configurations

### Minimal Project (Token-Conscious)

Disable everything that's project-specific:

```yaml
version: 1
disable:
  - swe/memory-protocol
  - swe/agent-model-routing
  - swe/vcs/git-conventions
  - ml/*
  - writing/*
```

**Token reduction:** ~5,047 (all blacklistable + path-scoped category blocks) → ~11,575 (core only)

### ML Project

Disable non-ML rules:

```yaml
version: 1
disable:
  - swe/memory-protocol
  - swe/agent-model-routing
  - writing/*
```

**Rationale:** This project uses its own model routing and experiment tracking; writing rules are out-of-scope. ML rules stay enabled for training discipline.

### Standard Project

No blacklist — accept all rules:

```yaml
# .claude/praxion-rules.yaml (empty or omitted entirely)
```

**Behavior:** Identical to current Praxion installations; all rules load.

## Further Reading

- [Architecture Guide: Rules section](architecture.md#3-components) — technical components implementing the two-channel delivery
- [Onboarding: Rules Configuration](../commands/onboard-project.md) — how to add this to an existing project
- [rules/_manifest.yaml](../rules/_manifest.yaml) — machine-readable rule taxonomy (auto-generated)
- [Example Configuration](../claude/config/praxion-rules.yaml.example) — template shipped by Praxion; copy to your project's `.claude/praxion-rules.yaml` and edit the `disable:` list
