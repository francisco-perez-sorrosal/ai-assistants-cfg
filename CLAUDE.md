# ai-assistants

The operational infrastructure for the development philosophy defined in `~/.claude/CLAUDE.md`. This repo provides the skills, agents, rules, commands, and MCP servers that make the philosophy actionable across projects.

## How the Ecosystem Serves the Philosophy

| Principle | Operationalized By |
|---|---|
| **Context engineering** | Skills — right domain knowledge loaded on demand via progressive disclosure |
| **Understand, Plan, Verify** | Agent pipeline — from ideation through verification, each agent owning one phase |
| **Conventions and consistency** | Rules — coding style, git hygiene, coordination protocols enforced automatically |
| **Learning loop** | Memory MCP + `LEARNINGS.md` — persistent knowledge across sessions, ephemeral within pipelines |
| **Frequent workflows** | Commands — commits, worktrees, scaffolding, memory management as repeatable actions |

The ecosystem is auto-discovered. Skills, agents, rules, and commands are never enumerated in always-loaded context — Claude finds them via filesystem scanning. `README.md` and per-directory READMEs are the human-facing catalogs.

## Working Here

- Load the matching crafting skill before modifying any component: `skill-crafting` for skills, `agent-crafting` for agents, `command-crafting` for commands, `rule-crafting` for rules
- **Never modify `~/.claude/plugins/cache/`** — edit source files in this repo; installed copies get overwritten on reinstall
- **Token budget**: Always-loaded content (CLAUDE.md files + rules) must stay under 8,500 tokens (~29,750 chars). Prefer skills with reference files for procedural content; reserve rules for declarative domain knowledge
- See `README.md` for user-facing docs, `README_DEV.md` for contributor conventions, `skills/README.md` for the skill catalog

## Session Protocol

At session start, call `session_start` on the memory MCP to load context about the user, project conventions, and past learnings. If `memories.assistant.name` is missing, pick a random name and store it immediately. Use memory MCP tools proactively during the session to store discoveries. Be curious about the user — learn their interests, background, and working style over time.

## Design Principles

- **Assistant-agnostic shared assets**: `skills/`, `commands/`, `agents/` at the repo root, reusable across tools
- **Assistant-specific config in subdirectories**: `claude/config/` for Claude, `cursor/config/` for Cursor
- **Progressive disclosure**: Skills load metadata at startup, full content on activation, reference files on demand — keeping token cost minimal
- **Auto-discovery over enumeration**: Components discovered via filesystem scanning; enumerating them in always-loaded context wastes tokens and creates sync burden
