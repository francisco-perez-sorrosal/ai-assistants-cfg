# Agent Instructions for Praxion

Praxion is a meta-project for building and governing other projects through
reusable agentic coding artifacts. It is mainly developed and operated through
Claude today, but its shared assets are intended to be reusable across agentic
coding frameworks such as Codex, Cursor, and Claude.

This file is an adapter for agents that understand `AGENTS.md`. It must avoid
textual redundancy with the existing Praxion guidance. The source of truth
remains the repository artifacts: `CLAUDE.md`, `rules/`, `skills/`, `commands/`,
`agents/`, hooks, MCP servers, and `.ai-state/`.

## Reading Order

1. Read `CLAUDE.md` first for Praxion-specific baseline context.
2. Read relevant always-on rules in `rules/**/*.md` that do not have `paths:`
   frontmatter when the work depends on project conventions.
3. Read path-scoped rules when touching matching files.
4. Load `skills/<name>/SKILL.md` when the task matches the skill description or
   the user names the skill.
5. Load skill references only on demand.
6. Treat `commands/*.md` and `agents/*.md` as executable workflow specs, not as
   Codex-native slash commands or subagents unless a Codex bridge explicitly
   implements that mapping.

## Operating Contract

Follow Praxion's behavioral contract from
`rules/swe/agent-behavioral-contract.md`:

- Surface Assumptions.
- Register Objection.
- Stay Surgical.
- Simplicity First.

For task sizing, follow `rules/swe/swe-agent-coordination-protocol.md`.
Default to the lowest process tier that fits the request. Use the existing
Praxion worktree home, `.claude/worktrees/<slug>/`, for isolated work.

## Interop Boundaries

- Do not duplicate existing Praxion guidance here. Point to source artifacts and
  load them on demand.
- Do not duplicate large rule, skill, command, or agent bodies into Codex files.
  Link to the existing artifacts and load them progressively.
- Do not modify `~/.claude/plugins/cache/`; edit source files in this repo.
- Keep assistant-specific configuration in assistant-specific directories.
  Shared assets remain at the repository root.
- Preserve the token-budget discipline for always-loaded guidance. Add detail to
  skills or references instead of this file when possible.

## Compatibility Contract

`AGENTS.md` is a compatibility shim, not a parallel instruction corpus. Its job
is to make the existing Praxion artifacts discoverable to agents that support
the `AGENTS.md` protocol, and to name the adapter seams for artifacts that are
not natively understood.

Directly reusable by AGENTS.md-aware coding agents without a tool-specific
installer:

- `AGENTS.md` as the entrypoint adapter.
- `CLAUDE.md` as project baseline context, read by reference.
- `rules/**/*.md` as conventions, loaded by reading the relevant files.
- `skills/*/SKILL.md` and skill references as progressive-disclosure guidance.
- Human-facing docs such as `README.md`, `README_DEV.md`, and `docs/`.
- Source code, tests, hooks, scripts, MCP server source, and `.ai-state/` data
  as normal repository files.

Requires an adapter or tool-specific installer before it becomes native in a
given agentic coding framework:

- `commands/*.md` -> slash-command exporter or installer.
- `agents/*.md` -> framework-specific subagent registration that preserves
  Praxion pipeline semantics.
- `rules/**/*.md` frontmatter -> path matcher and rule loader.
- `skills/*/SKILL.md` metadata -> skill discovery and activation bridge.
- MCP server manifests/source -> target framework MCP config writer.
- hooks -> target framework lifecycle hook integration.
- Assistant-specific config under `claude/`, `cursor/`, or future
  tool-specific directories.

## Verification

Use the verification path documented in `CLAUDE.md` for the files touched. For
changes to shipped blocks or onboarding behavior, run:

- `python3 scripts/sync_canonical_blocks.py --check`

For Python behavior, run the relevant pytest target from `CLAUDE.md` or
`README_DEV.md`.
