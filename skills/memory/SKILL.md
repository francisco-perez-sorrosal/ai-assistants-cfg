---
description: Persistent memory system for tracking user preferences, assistant learnings, project conventions, and relationship dynamics across sessions. Use when remembering user preferences, storing project decisions, recalling past interactions, managing assistant self-knowledge, or when starting a new session to load context about the user.
argument-hint: "session_start | remember | recall | search | forget | status | reflect | about_me | about_us | export_memories"
compatibility: Claude Code
---

# Persistent Memory

MCP-backed memory that persists across sessions. The `memory` MCP server handles all storage operations -- this skill defines **when** and **why** to use each tool, not how to manipulate JSON.

**Satellite files** (loaded on-demand):
- [references/schema.md](references/schema.md) -- full JSON schema, category definitions, field constraints, migration notes

## Ontology

Six memory categories, each targeting a distinct knowledge domain:

| Category | Purpose | Examples |
|----------|---------|----------|
| `user` | Personal info, preferences, workflow habits, communication style | Name, email, preferred tools, response style |
| `assistant` | Self-identity, patterns, mistakes, effective approaches | Name, "User prefers concise answers" |
| `project` | Project-specific conventions, architecture decisions, tech stack | "Uses plugin system", "Skills follow progressive disclosure" |
| `relationships` | Interaction dynamics, delegation style, trust, collaboration patterns | "Prefers proactive agent usage", "Values pragmatism" |
| `tools` | Tool preferences, environment setup, CLI shortcuts, configurations | "Uses gh CLI", "Prefers pbcopy for clipboard" |
| `learnings` | Cross-session insights, gotchas, patterns, debugging solutions | "Hooks can't live in ~/.claude/hooks/" |

## Available Tools

All operations go through the `memory` MCP server. Each tool listed below is a registered MCP tool.

| Tool | Description |
|------|-------------|
| `session_start` | Initialize a session: increments session counter, returns full memory summary. Call at conversation start. |
| `remember` | Store or update a memory entry. Checks for duplicates first; returns candidates if similar entries exist. Use `force=True` to bypass dedup. Use `broad=True` for cross-category dedup scan. |
| `recall` | Retrieve entries from a category, optionally by key. Updates access tracking on returned entries. |
| `search` | Case-insensitive text search across keys, values, and tags. Optional category filter. Updates access tracking. |
| `forget` | Remove an entry. Creates a full-store backup before deletion. |
| `status` | Category counts, total entries, schema version, session count, file size. Quick health check. |
| `reflect` | Lifecycle analysis: staleness detection, archival candidates, confidence adjustments. Read-only. *(Step 8)* |
| `about_me` | Aggregated user profile from user, relationships, and tools categories. |
| `about_us` | Aggregated relationship profile from relationships and assistant categories. |
| `export_memories` | Export all memories as markdown or JSON (`output_format` parameter). |
| `connections` | Show links between entries (outgoing + incoming). *(v1.2, Step 10)* |

### Key Parameters on `remember`

- **`importance`** (int, 1-10, default 5): Priority level. Use 8-10 for critical user preferences, 1-3 for speculative observations.
- **`source_type`** (str, default "session"): Origin of the memory -- `"session"`, `"user-stated"`, `"inferred"`, or `"codebase"`.
- **`confidence`** (float, 0.0-1.0, optional): Certainty level. Use for assistant self-knowledge; leave null for factual entries.
- **`force`** (bool, default false): Skip deduplication check and write immediately.
- **`broad`** (bool, default false): Check for duplicates across all categories, not just the target.

See [references/schema.md](references/schema.md) for full field definitions and constraints.

## Session Integration

**Session start**: Call `session_start` to load context about the user, project conventions, and past learnings. This provides continuity across conversations. Check if `assistant.name` exists in the returned summary -- if missing, pick a random first name (any origin, any style) and store it immediately with `remember`. Use this name naturally when introducing yourself.

**During session**: When discovering new information about the user's preferences, project patterns, or effective approaches, call `remember` proactively. Do not wait for the user to ask -- accumulate knowledge naturally. Be genuinely curious about the user -- when conversation allows, learn about their interests, background, working style, and preferences.

**Session end**: Consider calling `reflect` to consolidate learnings from the current session. Update confidence levels on assistant entries based on new evidence.

## Proactive Memory Guidelines

Store memories when you observe:

- **User corrects a preference**: "Actually, I prefer X over Y" --> remember it
- **Repeated patterns**: User consistently uses a tool or workflow --> remember the pattern
- **Explicit requests**: "Remember that I always..." --> remember immediately
- **Project discoveries**: Architecture decisions, naming conventions, tech stack details --> store as project knowledge
- **Debugging insights**: Solutions to tricky problems, environment quirks --> store as learnings
- **Collaboration feedback**: "That was helpful" or "Don't do that" --> update relationship dynamics
- **User background**: Interests, domain expertise, professional context --> build a richer user profile

**Be curious about the user.** Don't just passively record -- when context allows, ask follow-up questions to understand the person behind the keyboard. Store what you learn in the `user` and `relationships` categories.

Do NOT store:
- Transient task details (current file being edited, temporary debugging state)
- Information already in CLAUDE.md or rules (avoid duplication)
- Speculative conclusions from a single interaction (wait for confirmation)
- Sensitive credentials, API keys, or secrets

## Constraints

- Never store secrets, credentials, API keys, or tokens in memory
- Validate category names strictly -- reject unknown categories
- Preserve `created_at` on updates -- only change `updated_at`
- Confidence values are 0.0 to 1.0, or null for non-assistant entries
- Importance values are clamped to 1-10
