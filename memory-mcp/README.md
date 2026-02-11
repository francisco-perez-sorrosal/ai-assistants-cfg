# Memory MCP Server

Persistent, intelligent memory for AI coding assistants. An MCP server that stores memories in a JSON file with deduplication-on-write, access tracking, ranked search, lifecycle analysis, and cross-reference links.

## Quick Start

The `i-am` plugin auto-registers the MCP server on install. The server starts automatically via stdio transport when Claude Code calls any memory tool -- no manual setup required.

To run standalone (without the plugin):

```bash
cd memory-mcp
uv run python -m memory_mcp
```

## MCP Server Registration

The server is declared in `.claude-plugin/plugin.json` under `mcpServers`:

```json
"memory": {
  "command": "uv",
  "args": ["run", "--project", "${CLAUDE_PLUGIN_ROOT}/memory-mcp", "python", "-m", "memory_mcp"],
  "env": { "MEMORY_FILE": ".ai-state/memory.json" }
}
```

All agents (main and sub-agents) access memory tools through the plugin system without loading the memory skill.

## MCP Tools

12 tools registered on the `Memory` FastMCP server:

| Tool | Parameters | Description |
|------|-----------|-------------|
| `session_start` | *(none)* | Increment session counter, return full memory summary with category counts |
| `remember` | `category`, `key`, `value`, `tags?`, `importance?`, `source_type?`, `confidence?`, `force?`, `broad?` | Store or update a memory entry with dedup-on-write |
| `forget` | `category`, `key` | Remove an entry (creates backup, cleans incoming links) |
| `recall` | `category`, `key?` | Retrieve entries with access tracking |
| `search` | `query`, `category?` | Multi-signal ranked search across keys, values, and tags |
| `status` | *(none)* | Category counts, total entries, schema version, session count, file size |
| `export_memories` | `output_format?` | Export all memories as markdown (default) or JSON |
| `about_me` | *(none)* | Aggregated user profile from user, relationships, and tools categories |
| `about_us` | *(none)* | Aggregated user-assistant relationship profile |
| `reflect` | *(none)* | Lifecycle analysis: stale entries, archival candidates, confidence adjustments (read-only) |
| `connections` | `category`, `key` | Show outgoing and incoming links for an entry |
| `add_link` | `source_category`, `source_key`, `target_category`, `target_key`, `relation` | Create a unidirectional link between entries |
| `remove_link` | `source_category`, `source_key`, `target_category`, `target_key` | Remove a link between entries |

## MCP Resources

| URI | Description |
|-----|-------------|
| `memory://schema` | Schema version, valid categories, statuses, relations, and field documentation |
| `memory://stats` | Category counts, total entries, session count, file size |

Resources are read-only endpoints with no side effects. Use tools for operations that require access tracking.

## Schema

**Version**: 1.2

**Categories**: `user`, `assistant`, `project`, `relationships`, `tools`, `learnings`

Each memory entry contains:

| Field | Type | Description |
|-------|------|-------------|
| `value` | string | The memory content |
| `created_at` | ISO 8601 | Creation timestamp (UTC) |
| `updated_at` | ISO 8601 | Last modification timestamp (UTC) |
| `tags` | string[] | Tags for categorization and search |
| `importance` | int (1-10) | Priority level, default 5 |
| `confidence` | float (0.0-1.0) | Certainty level, null if unset |
| `source` | `{type, detail}` | Origin metadata: `session`, `user-stated`, `inferred`, or `codebase` |
| `access_count` | int | Times recalled or searched |
| `last_accessed` | ISO 8601 | Last access timestamp, null if never |
| `status` | string | Lifecycle state: `active`, `archived`, or `superseded` |
| `links` | array | `[{target: "category.key", relation: "..."}]` |

**Valid relations**: `supersedes`, `elaborates`, `contradicts`, `related-to`, `depends-on`

## Key Features

**Dedup-on-write**: `remember` scans the target category for overlapping entries (tag overlap, value similarity) before writing. Returns candidates with an ADD/UPDATE/NOOP recommendation. Use `force=True` to bypass, `broad=True` for cross-category scan.

**Access tracking**: `recall` and `search` increment `access_count` and update `last_accessed` on every returned entry. This drives lifecycle analysis and search ranking.

**Ranked search**: Results scored by weighted combination of text match quality (0.4), tag overlap (0.2), importance (0.25), and recency (0.15). Recency uses exponential decay with ~21-day half-life.

**Lifecycle reflect**: Read-only analysis that flags stale entries (never accessed, 7+ days old), archival candidates (low importance, never accessed), and proposes confidence adjustments based on access patterns and source type.

**Cross-reference links**: Unidirectional links between entries with five relation types. `remember` auto-creates `related-to` links when a new entry shares 2+ tags with existing entries in the same category. `connections` provides reverse lookup.

**Atomic writes**: All mutations use write-to-temp + `os.replace()` with `fcntl.flock()` for concurrent access safety.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_FILE` | `.ai-state/memory.json` | Path to the JSON memory file |

## Schema Migration

The server auto-migrates on first load:

- **v1.0 to v1.1**: Adds `importance`, `source`, `access_count`, `last_accessed`, `status`, `session_count`
- **v1.1 to v1.2**: Adds `links` field to every entry

Pre-migration backups are created before each migration step (`.pre-migration-1.0.json`, `.pre-migration-1.1.json`).

## Development

Run tests:

```bash
cd memory-mcp
uv run pytest -v
```

See [README_DEV.md](README_DEV.md) for architecture details and contributor guide.
