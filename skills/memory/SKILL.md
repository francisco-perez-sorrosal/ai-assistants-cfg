---
description: Persistent memory system for tracking user preferences, assistant learnings, project conventions, and relationship dynamics across sessions. Use when remembering user preferences, storing project decisions, recalling past interactions, managing assistant self-knowledge, or when starting a new session to load context about the user.
argument-hint: "init|remember|forget|recall|status|export|about-me|about-us|search|reflect [args]"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Persistent Memory

Structured, JSON-backed memory that persists across sessions. Complements Claude Code's built-in memory (`MEMORY.md`) with a queryable, categorized store for user preferences, assistant learnings, project conventions, and relationship dynamics.

**Satellite files** (loaded on-demand):
- [references/schema.md](references/schema.md) -- full JSON schema, category definitions, field constraints, migration notes

## Storage

- **Location**: `.ai-state/memory.json` (committed to git, versioned)
- **Format**: JSON with schema version for future migrations
- **Backups**: Auto-created at `.ai-state/memory.backup.json` before destructive operations

## Ontology

Six memory categories, each targeting a distinct knowledge domain:

| Category | Purpose | Examples |
|----------|---------|----------|
| `user` | Personal info (name, surname, alias), preferences, workflow habits, communication style | First name, last name, username (alias), email, preferred tools, response style |
| `assistant` | Self-identity, self-knowledge about patterns, mistakes, effective approaches | Name, "User prefers concise answers", "This codebase uses pixi" |
| `project` | Project-specific conventions, architecture decisions, tech stack | "Uses plugin system", "Skills follow progressive disclosure" |
| `relationships` | Interaction dynamics, delegation style, trust, collaboration patterns | "Prefers proactive agent usage", "Values pragmatism" |
| `tools` | Tool preferences, environment setup, CLI shortcuts, configurations | "Uses gh CLI", "Prefers pbcopy for clipboard" |
| `learnings` | Cross-session insights, gotchas, patterns, debugging solutions | "Hooks can't live in ~/.claude/hooks/", "Plugin cache paths change" |

Each entry has: `key`, `value`, `category`, `created_at`, `updated_at`, optional `tags[]`, optional `confidence` (0.0-1.0, for assistant self-knowledge).

See [references/schema.md](references/schema.md) for the full JSON schema and field constraints.

## Subcommands

Invoke via the `/memory` command or by activating this skill directly. All subcommands operate on `.ai-state/memory.json`.

### init

Initialize the memory store. Creates `.ai-state/memory.json` with the schema structure if it does not exist. Safe to run multiple times -- skips if the file already exists.

**Procedure:**

1. Check if `.ai-state/memory.json` exists
2. If not, create it with the empty schema structure:
   ```json
   {
     "schema_version": "1.0",
     "memories": {
       "user": {},
       "assistant": {},
       "project": {},
       "relationships": {},
       "tools": {},
       "learnings": {}
     }
   }
   ```
3. If it exists, report current status instead

### remember `<category>` `<key>` `<value>`

Store or update a memory entry. If the key already exists in the category, update its value and `updated_at` timestamp. Merges tags if provided.

**Procedure:**

1. Read `.ai-state/memory.json`
2. Validate `category` is one of the six defined categories
3. Create or update the entry:
   ```json
   {
     "value": "<value>",
     "created_at": "<ISO 8601 UTC>",
     "updated_at": "<ISO 8601 UTC>",
     "tags": [],
     "confidence": null
   }
   ```
4. For updates: preserve `created_at`, update `updated_at`, merge new tags with existing
5. Write the updated JSON back

**Optional flags:**
- Tags: include `[tag1, tag2]` after the value to tag the entry
- Confidence: include `confidence:0.8` for assistant self-knowledge entries

### forget `<category>` `<key>`

Remove a memory entry. Creates a backup before deletion.

**Procedure:**

1. Read `.ai-state/memory.json`
2. Copy current file to `.ai-state/memory.backup.json`
3. Remove the entry at `memories.<category>.<key>`
4. Write the updated JSON back
5. Confirm what was removed

### recall `<category>` `[key]`

Retrieve memories. Without a key, returns all entries in the category. With a key, returns that specific entry.

**Procedure:**

1. Read `.ai-state/memory.json`
2. If key provided: return `memories.<category>.<key>` (or "not found")
3. If no key: return all entries in `memories.<category>` as a formatted list
4. Display each entry with its value, tags, confidence (if set), and timestamps

### status

Show memory statistics: entry counts per category, total entries, last updated timestamp, file size.

**Procedure:**

1. Read `.ai-state/memory.json`
2. Count entries per category
3. Find the most recent `updated_at` across all entries
4. Check file size with `ls -lh .ai-state/memory.json`
5. Display a summary table:
   ```
   Category       Count  Last Updated
   user           5      2026-02-09T14:30:00Z
   assistant      3      2026-02-09T15:00:00Z
   ...
   Total: 15 entries | File: 2.1 KB | Schema: v1.0
   ```

### export

Export all memories as formatted markdown, suitable for sharing or review.

**Procedure:**

1. Read `.ai-state/memory.json`
2. Generate markdown with one section per category:
   ```markdown
   ## User
   - **username**: @fperezsorrosal [personal]
   - **email**: fperezsorrosal@gmail.com [personal]

   ## Assistant
   - **response_style**: Concise and direct (confidence: 0.9) [communication]
   ```
3. Output to stdout (do not write a file unless the user requests it)

### about-me

Show everything known about the user -- aggregates entries from the `user` category plus user-related entries from `relationships` and `tools`.

**Procedure:**

1. Read `.ai-state/memory.json`
2. Display all `user` category entries
3. Display `relationships` entries tagged with `user-facing`
4. Display `tools` entries tagged with `user-preference`
5. Format as a coherent profile summary

### about-us

Show the relationship profile -- how the user and assistant work together.

**Procedure:**

1. Read `.ai-state/memory.json`
2. Display all `relationships` category entries
3. Include relevant `assistant` entries about interaction patterns
4. Format as a collaboration profile

### search `<query>`

Full-text search across all memories. Searches keys, values, and tags.

**Procedure:**

1. Read `.ai-state/memory.json`
2. Search across all categories for entries where the query matches (case-insensitive):
   - The key name
   - The value text
   - Any tag
3. Display matching entries grouped by category with the matching text highlighted

### reflect

Assistant reviews its accumulated knowledge and patterns. This is a self-assessment subcommand.

**Procedure:**

1. Read `.ai-state/memory.json`
2. Review all `assistant` and `learnings` entries
3. Identify:
   - Entries with low confidence that could be updated based on recent interactions
   - Contradictory entries across categories
   - Gaps -- areas where more knowledge would be useful
   - Stale entries that may no longer be accurate
4. Produce a brief reflection summary
5. Optionally propose updates (with user approval before executing)

## Session Integration

This skill works best when integrated into the session lifecycle:

**Session start**: Read `.ai-state/memory.json` to load context about the user, project conventions, and past learnings. This provides continuity across conversations without requiring the user to re-explain preferences. Check `memories.assistant.name` -- if it is missing, pick a random first name for yourself (any origin, any style -- be creative) and store it immediately with `remember assistant name "<chosen-name>"`. Use this name naturally when introducing yourself or when the user asks who you are.

**During session**: When discovering new information about the user's preferences, project patterns, or effective approaches, store it proactively using `remember`. Do not wait for the user to ask -- accumulate knowledge naturally. Be genuinely curious about the user -- when conversation allows, learn about their interests, background, working style, and preferences. The richer the user profile, the better the collaboration.

**Session end**: Consider running `reflect` to consolidate learnings from the current session. Update confidence levels on assistant entries based on new evidence.

## Proactive Memory Guidelines

The assistant should store memories when it observes:

- **User corrects a preference**: "Actually, I prefer X over Y" --> remember it
- **Repeated patterns**: User consistently uses a tool or workflow --> remember the pattern
- **Explicit requests**: "Remember that I always..." --> remember immediately
- **Project discoveries**: Architecture decisions, naming conventions, tech stack details --> store as project knowledge
- **Debugging insights**: Solutions to tricky problems, environment quirks --> store as learnings
- **Collaboration feedback**: "That was helpful" or "Don't do that" --> update relationship dynamics
- **User background**: Interests, domain expertise, professional context, hobbies mentioned in passing --> build a richer user profile over time

**Be curious about the user.** Don't just passively record -- when context allows, ask follow-up questions to understand the person behind the keyboard. A well-rounded user profile makes every future interaction more effective. Store what you learn in the `user` and `relationships` categories.

Do NOT store:
- Transient task details (current file being edited, temporary debugging state)
- Information already in CLAUDE.md or rules (avoid duplication)
- Speculative conclusions from a single interaction (wait for confirmation)
- Sensitive credentials, API keys, or secrets

## Constraints

- Never store secrets, credentials, API keys, or tokens in memory
- Always create a backup before `forget` operations
- Validate category names strictly -- reject unknown categories
- Preserve `created_at` on updates -- only change `updated_at`
- Keep the JSON human-readable (2-space indentation)
- Confidence values are 0.0 to 1.0, or null for non-assistant entries
