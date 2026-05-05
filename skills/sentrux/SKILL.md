---
name: sentrux
description: >
  Sentrux structural quality sensor integration — the external Rust-native
  Claude Code marketplace plugin that scores code structure across modularity,
  acyclicity, depth, equality, and redundancy via 15 MCP tools. Covers when to
  call which tool, the session-bracketing pattern, the 0-10000 quality score,
  the metric-model drift between plugin manifest and binary, and Praxion's
  current advisory verifier integration. Use when bracketing agent coding
  sessions with structural quality measurements, interpreting `sentrux scan` /
  `health` / `architecture` output, authoring `.sentrux/rules.toml`, or
  deciding whether to elevate sentrux signals from advisory to gating.
allowed-tools: [Read, Grep, Bash, Write, Edit]
compatibility: Claude Code
---

# Sentrux Structural Quality Sensor

Sentrux is an external structural quality sensor for AI-agent coding sessions.
It is not a replacement for Praxion's existing signal stack (sentinel,
verifier, architect-validator, fitness functions); it fills a narrow gap none
of those cover: real-time, language-agnostic structural quality measurement
during the agent edit loop.

This skill captures Praxion's integration contract with sentrux — what is
installed, what is advisory, what is gating, and which policy decisions
remain open.

## 1. When to Use This Skill

- Before or after an agent coding session, when you want a structural quality
  delta (`session_start` / `session_end`)
- When interpreting `sentrux scan`, `health`, or `architecture` output
- When authoring or editing `.sentrux/rules.toml` (constraints, layers,
  boundaries)
- When the verifier emits a Phase 9b finding and you need to interpret it
- When deciding whether a sentrux finding should produce a tech-debt row
  (no agent currently does this — see § 7)

Do **not** use this skill to:

- Replace import-linter contracts — sentrux is structural-overall, import-linter
  is invariant-specific; both have a place
- Replace architect-validator — architect-validator audits the code↔DSL↔ADR
  triangle and requires a LikeC4 model; sentrux is language-agnostic and
  model-free
- Replace sentinel TD findings — sentrux is a candidate signal source for the
  TD dimension, but the TD dimension's classification logic is sentinel-owned

## 2. Prerequisites

| Layer | Mechanism | Without it |
|-------|-----------|------------|
| Binary | `brew install sentrux/tap/sentrux` (macOS) / curl installer (Linux) / Praxion's `install.sh` (default-skip prompt) | All sentrux features unavailable |
| Per-project rules | `.sentrux/rules.toml` rendered by `/onboard-project` Phase 8b.6 (default-skip), or hand-written from `claude/aac-templates/sentrux-rules.toml.tmpl` | `sentrux check .` exits 0 by default — no rule violations to detect |
| Marketplace plugin | `/plugin marketplace add sentrux/sentrux` then `/plugin install sentrux@sentrux-marketplace` (run inside Claude Code) | MCP tools unavailable in-session, but `sentrux check .` (CLI) still works |

When any prerequisite is absent, sentrux integration silently degrades — no
Praxion surface treats absence as a failure.

## 3. The 15 MCP Tools

When the marketplace plugin is installed, sentrux exposes these MCP tools:

| Tool | Purpose | When to call |
|------|---------|--------------|
| `scan` | Overview of the project's structural quality | Start of a session, or before deciding whether to dig deeper |
| `health` | 5-metric breakdown | When `scan` flagged a problem and you want to know where |
| `architecture` | Higher-level structural view | Reviewing module organization, layer adherence |
| `coupling` | Module-to-module coupling map | Refactoring decisions |
| `cycles` | Dependency cycle detection | Specific cycle hunting |
| `hottest` | Highest-coupling / highest-complexity files | Choosing where to invest refactoring effort |
| `dsm` | Dependency structure matrix | Auditing layering |
| `evolution` | Trend over time | Long-running projects, regression detection |
| `test_gaps` | Coverage-gap heuristic | Before authoring tests |
| `check_rules` | Validate `.sentrux/rules.toml` constraints | CI-style invocation |
| `session_start` | Begin an agent session window | Before the agent edits code |
| `session_end` | End an agent session window; emit before/after delta | After the agent finishes editing |
| `rescan` | Force a fresh scan (cache invalidate) | After major changes the cache may not have seen |
| `blast_radius` | Estimate downstream impact of changing a module | Refactoring planning |
| `level` | Structural-level placement for a file | Module organization decisions |

The README highlights nine of these as the primary lifecycle surface (`scan`,
`health`, `session_start`, `session_end`, `rescan`, `check_rules`, `evolution`,
`dsm`, `test_gaps`); the other six are diagnostic tools.

## 4. The 0-10000 Quality Score

Sentrux rolls five root-cause metrics — modularity, acyclicity, depth, equality,
redundancy — into a single 0-10000 score. Higher is better. The score is
returned by `scan` and by the `session_start` / `session_end` delta.

**Metric-model drift caveat (verified at upstream commit `28e644d`, March 2026).**
The sentrux plugin manifest still advertises "14 health dimensions graded A-F"
while the v0.5.7+ binary advertises "5 root-cause structural metrics" after the
"Sensor Overhaul." Both surfaces ship from the same repo. When automating
against sentrux output, do not depend on either count being stable across
versions; pin to a known-good `sentrux@<x.y.z>` if your CI gates on metric
counts.

## 5. Session Bracketing Pattern

The most useful integration shape is bracketing the agent's edit window:

```
session_start                  # capture pre-edit baseline
  ... agent edits code ...
session_end                    # emit delta + verdict
```

The verdict is `pass` (no regression) or `fail` (regression detected). The
pipeline-level interpretation of `fail` is an open policy decision (§ 7);
today, treat it as advisory.

## 6. Output Interpretation

`sentrux check .` (CLI) returns:

- exit 0 — all rules in `.sentrux/rules.toml` pass
- exit 1 — at least one rule failed (forbidden cycle, layer boundary
  violation, etc.)

`scan` (MCP) returns JSON of the form:

```json
{ "quality_signal": 7342, "files": 139, "bottleneck": "modularity" }
```

When a finding maps to a Praxion TECH_DEBT_LEDGER row, the natural class
mapping is `cyclic-dep` for cycle findings, `complexity` for high-coupling
findings, and `other` for residual structural-quality drift. **No Praxion
agent currently writes ledger rows from sentrux output** — this is an open
integration point (§ 7).

## 7. Open Policy Decisions

Five policy decisions are deferred to the systems-architect. Until resolved,
sentrux integration stays advisory at every Praxion surface that consumes it.

| ID | Decision | Default until resolved |
|----|----------|------------------------|
| Q1 | Version-pinning policy (latest vs. pinned `sentrux@<x.y.z>`) | latest |
| Q2 | Cursor / Windsurf install path (Phase 8b.6 emits Claude Code marketplace instructions only) | Claude Code only |
| Q3 | Vendor-skill coexistence — sentrux's bundled `scan` skill lands in user projects; sentinel / skill-genesis treatment is unspecified | sentinel ignores vendor skills |
| Q4 | Verifier elevation — should `sentrux check .` regression be FAIL, WARN, or invisible? | WARN (advisory, never FAIL) |
| Q5 | Baseline-degradation enforcement during pipelines (should the implementer be required to address regression before verifier sign-off?) | not enforced |

When the architect resolves any of these, this section updates.

## 8. Praxion Integration Points

### Active

- **`install.sh`** — opt-in (default-skip) install step for the binary
- **`/onboard-project` Phase 8b.6** — per-project `.sentrux/rules.toml` +
  emits marketplace plugin install instructions (opt-in within the AaC
  opt-in tier)
- **`agents/verifier.md` Phase 9b** — runs `sentrux check .` post-implementation,
  emits a single WARN finding on regression (never FAIL); skips silently when
  prerequisites are absent

### Deferred (pending policy decisions)

- Implementer step-level session bracketing (`session_start` / `session_end`)
- Sentinel TD-dimension ingest of `sentrux health` output
- TECH_DEBT_LEDGER auto-population from sentrux findings
- Pre-commit hook block invoking `sentrux check .`

When any of Q1-Q5 above resolves, the matching deferred integration shape
lands as a follow-up commit and updates this section.

## 9. Sources

- [sentrux/sentrux repo](https://github.com/sentrux/sentrux)
- [marketplace plugin commit `28e644d`](https://github.com/sentrux/sentrux/commit/28e644de6a23c64362ed888e99919767fd25893e) — adds `.claude-plugin/marketplace.json`, plugin manifest, `.mcp.json`, and bundled `scan` skill
