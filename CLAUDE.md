# ai-assistants

The operational infrastructure for the development philosophy defined in `~/.claude/CLAUDE.md`. This repo provides the skills, agents, rules, commands, and MCP servers that make the philosophy actionable across projects.

## How the Ecosystem Serves the Philosophy

See the mapping table in `~/.claude/CLAUDE.md` under "The Ecosystem as Philosophy's Implementation." This repo is where those components live — skills, agents, rules, commands, and MCP servers are all authored and maintained here.

## Working Here

- Load the matching crafting skill before modifying any component: `skill-crafting` for skills, `agent-crafting` for agents, `command-crafting` for commands, `rule-crafting` for rules
- **Never modify `~/.claude/plugins/cache/`** — edit source files in this repo; installed copies get overwritten on reinstall
- **Token budget**: Always-loaded content (CLAUDE.md files + rules) must stay under 8,500 tokens (~29,750 chars). Prefer skills with reference files for procedural content; reserve rules for declarative domain knowledge
- See `README.md` for user-facing docs, `README_DEV.md` for contributor conventions, `skills/README.md` for the skill catalog

## Session Protocol

At session start, call `session_start` on the memory MCP to load context about the user, project conventions, and past learnings (Recall). Store discoveries proactively during the session (Learn). Apply past insights to current tasks (Apply). This implements the Learning Loop from the global philosophy.

If `memories.assistant.name` is missing, pick a random name and store it immediately. Be curious about the user — learn their interests, background, and working style over time.

## Design Principles

- **Assistant-agnostic shared assets**: `skills/`, `commands/`, `agents/` at the repo root, reusable across tools
- **Assistant-specific config in subdirectories**: `claude/config/` for Claude, `cursor/config/` for Cursor
- **Progressive disclosure**: Skills load metadata at startup, full content on activation, reference files on demand — keeping token cost minimal
