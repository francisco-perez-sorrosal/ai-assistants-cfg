# Memory Skill

Persistent, structured memory system that tracks user preferences, assistant learnings, project conventions, and relationship dynamics across sessions. Stores data in `.ai-state/memory.json` as a categorized, queryable JSON document.

Complements Claude Code's built-in `MEMORY.md` (unstructured, auto-managed) with explicit categories, tags, confidence levels, and subcommands for retrieval and introspection.

## When to Use

- Starting a new session and loading context about the user and past interactions
- Storing user preferences, project conventions, or workflow discoveries
- Recalling what the assistant knows about the user or project
- Managing assistant self-knowledge (patterns, effective approaches, mistakes)
- Searching across accumulated knowledge from past sessions
- Reviewing and consolidating cross-session learnings

## Activation

The skill activates automatically when the agent detects memory-related tasks: remembering preferences, recalling past knowledge, user profile queries, or session context loading.

Trigger explicitly via the `/memory` command with a subcommand:

```
/memory init
/memory remember user timezone "America/Los_Angeles"
/memory recall user
/memory about-me
/memory search "python"
/memory reflect
```

## Skill Contents

| File | Purpose |
|------|---------|
| `SKILL.md` | Core reference: ontology, subcommand procedures, session integration, proactive memory guidelines |
| `references/schema.md` | Full JSON schema, category definitions, field constraints, migration notes |
| `README.md` | This file -- overview and usage guide |

## Data Model

Six categories, each stored as a keyed object in `.ai-state/memory.json`:

| Category | Tracks |
|----------|--------|
| `user` | Personal info, preferences, workflow habits |
| `assistant` | Self-knowledge about patterns, mistakes, effective approaches |
| `project` | Conventions, architecture decisions, tech stack |
| `relationships` | Interaction dynamics, delegation style, trust |
| `tools` | Tool preferences, environment setup, CLI shortcuts |
| `learnings` | Cross-session insights, gotchas, debugging solutions |

## Subcommands

| Subcommand | Arguments | Description |
|------------|-----------|-------------|
| `init` | -- | Initialize memory store (safe to re-run) |
| `remember` | `<category> <key> <value>` | Store or update a memory entry |
| `forget` | `<category> <key>` | Remove an entry (creates backup first) |
| `recall` | `<category> [key]` | Retrieve entries (all in category or specific key) |
| `status` | -- | Show entry counts, last updated, file size |
| `export` | -- | Export all memories as formatted markdown |
| `about-me` | -- | Show everything known about the user |
| `about-us` | -- | Show the relationship and collaboration profile |
| `search` | `<query>` | Full-text search across all memories |
| `reflect` | -- | Assistant reviews and consolidates its knowledge |

## Related Artifacts

- [`/memory` command](../../commands/memory.md) -- slash command that delegates to this skill
- [`.ai-state/memory.json`](../../.ai-state/memory.json) -- the persistent data store
