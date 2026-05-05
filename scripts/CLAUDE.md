# Scripts

Utility and operational scripts for the Praxion ecosystem.

## Available Scripts

- `praxion-claude-dev` — Launch Claude Code with the Praxion working tree as the plugin source (wraps `claude --plugin-dir`). Passes `--dangerously-skip-permissions` by default; set `PRAXION_DEV_SAFE=1` to keep prompts. See [Session-scoped local testing](../README_DEV.md#session-scoped-local-testing)
- `ccwt` — Claude Code Worktrees: opens a tmux session with one pane per git worktree, each running Claude Code
- `chronograph-ctl` — Development helper for the Task Chronograph MCP server (start/stop/restart/status/logs from source)
- `phoenix-ctl` — Manage the Phoenix observability daemon (install/start/stop/restart/status/uninstall via launchd)
- `reconcile_ai_state.py` — Post-merge reconciliation for `.ai-state/` artifacts: semantic memory.json merge, observations.jsonl dedup, ADR renumbering, index regeneration. Called by `/merge-worktree`
- `regenerate_adr_index.py` — Regenerate `.ai-state/decisions/DECISIONS_INDEX.md` from ADR file frontmatter
- `finalize_adrs.py` — Promote fragment ADRs under `.ai-state/decisions/drafts/` to stable `<NNN>-<slug>.md`, rewrite `dec-draft-<hash>` cross-references across sibling ADRs / `.ai-work/*/LEARNINGS.md` / `SYSTEMS_PLAN.md` / `IMPLEMENTATION_PLAN.md`, regenerate the index. Idempotent; advisory file lock. Invoked by the finalize hook chain (post-merge / post-commit / post-checkout) and `/merge-worktree`
- `finalize_tech_debt_ledger.py` — Collapse duplicate rows in `.ai-state/TECH_DEBT_LEDGER.md` by `dedup_key`. Status precedence on collapse is `resolved > in-flight > open > wontfix`; tie-break by newer `last-seen`; non-conflicting fields merged (earliest `first-seen`; notes concatenated with ` // `; locations union-sorted). Idempotent; advisory file lock; fail-loud on malformed rows (exit 1). Invoked by the finalize hook chain after `finalize_adrs.py`. See `rules/swe/agent-intermediate-documents.md` § `TECH_DEBT_LEDGER.md`
- `check_squash_safety.py` — Post-merge diagnostic: detect `.ai-state/` entry erasure from squash-merges and emit a recovery warning. Non-blocking (exit 0). Invoked by the post-merge entry of the finalize hook chain after finalize
- `finalize_chain.sh` — Sourceable bash library: shared library powering the finalize hook chain. Path resolution that follows symlinks (works for both copy-installed and symlink-installed hooks), state-driven gate predicates (`on_main`, `drafts_present`, `state_was_touched`), and the three public entry points consumed by the dispatcher: `finalize_chain_post_merge`, `finalize_chain_post_commit`, `finalize_chain_post_checkout`. State-triggered semantics ensure draft ADRs landing on main via any path eventually promote
- `git-finalize-hook.sh` — Multiplexed git hook dispatcher. A single script handles three triggers (post-merge, post-commit, post-checkout); each `.git/hooks/<name>` is a symlink pointing here, and dispatch reads `basename($0)` to select the matching entry point in `finalize_chain.sh`. Replaces the prior single-trigger `git-post-merge-hook.sh`
- `check_id_citation_discipline.py` — Inbound id-citation discipline check: scans committed code files for ephemeral identifier citations that must not appear in source. Wired into `hooks/commit_gate.sh` on `git commit`. Parallel to the outbound `check_shipped_artifact_isolation.py`. See `rules/swe/id-citation-discipline.md`
- `check_shipped_artifact_isolation.py` — Outbound shipped-artifact isolation check: scans shipped artifact surfaces for references to specific pipeline/state entries. Wired into `hooks/commit_gate.sh`. See `rules/swe/shipped-artifact-isolation.md`
- `check_aac_golden_rule.py` — AaC golden-rule enforcement: detects staged generated-artifact edits (`docs/diagrams/<name>/<view>.{d2,svg}` or content inside `<!-- aac:generated -->` fences) without a co-staged source change. Gate mode (`--mode=gate`, default) wired into `git-pre-commit-hook.sh` Block D; audit mode (`--mode=audit --json`) consumed by sentinel EC07. Stdlib-only; side-effect-free. See `rules/writing/aac-dac-conventions.md`
- `migrate_worktree_home.sh` — Print copy-paste-ready `git worktree move` commands to migrate legacy `.trees/<name>/` worktrees to `.claude/worktrees/<name>/`. Performs no automatic move
- `sentrux_history.py` — Run `sentrux check .` and write a per-run report triple under `.ai-state/metrics_reports/`: `SENTRUX_REPORT_<timestamp>.json` + `.md` (per-run pair) and one appended row in `SENTRUX_HISTORY.md` (aggregate log mirroring `METRICS_LOG.md`'s shape so the bundled viewer at `.ai-state/metrics_reports/index.html` can render it as a side-car panel). Stdlib-only; defensive parsing of sentrux's text output (no `--json` flag in v0.5.7); returns the sentrux exit code so callers can fail-fast on rule violations while still landing the triple

## Conventions

- Shell scripts (bash), `set -euo pipefail` (except `ccwt` which uses `set -eo pipefail`)
- Each script is self-contained with usage documentation in header comments
- `chronograph-ctl` and `phoenix-ctl` are development/operations tools — in production, MCP servers run via plugin.json

## Installer Filter

`install_claude.sh` links scripts under `~/.local/bin/` only when they are `-f && -x` AND do not match `merge_driver_*` or `git-*-hook.sh`. User-facing tools must be executable (`chmod +x`); merge drivers and git hooks are invoked by git, not by PATH, so they are intentionally skipped. Orphaned symlinks (from renamed/removed scripts) are cleaned on upgrade by `clean_stale_symlinks`. See dec-042.

## Wired into Onboarding

The `/onboard-project` command installs several of these scripts as git hooks and merge drivers in user projects. When changing any of them, verify the onboarding flow's expectations still hold:

- `git-finalize-hook.sh` + `finalize_chain.sh` — symlinked into `.git/hooks/{post-merge,post-commit,post-checkout}` by `/onboard-project` Phase 4 (state-driven finalize chain — every path landing drafts on main eventually triggers one of the three hooks)
- `git-pre-commit-hook.sh` — Praxion-author-only (shipped-artifact isolation). User projects get a *tailored* inline hook script written by Phase 4 that runs only `check_id_citation_discipline.py` — Praxion's shipped-artifact concern doesn't apply downstream
- `merge_driver_memory.py`, `merge_driver_observations.py` — registered via `git config merge.<name>.driver` by `/onboard-project` Phase 3 (alongside the `.gitattributes` entries)
- `check_id_citation_discipline.py` — invoked by the user-project pre-commit hook installed in Phase 4
- `finalize_adrs.py`, `finalize_tech_debt_ledger.py`, `reconcile_ai_state.py`, `check_squash_safety.py` — invoked by the finalize hook chain (composition varies per trigger; see `finalize_chain.sh`)

Path or interface changes to these scripts must update `/onboard-project` Phase 3 (`git config` driver line) and Phase 4 (inline pre-commit hook body) to match.
