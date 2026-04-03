# Memory MCP Server

Persistent, intelligent memory for AI coding assistants. **Tool-agnostic:** used by **Claude Code** (plugin) and **Cursor** (via `./install.sh cursor`). Dual-layer architecture: curated memories in JSON (`memory.json`) and automatic observations in JSONL (`observations.jsonl`). Features deduplication-on-write, access tracking, ranked search, lifecycle analysis, temporal supersession, structured consolidation, cross-reference links, chronological timelines, and session narratives.

## Quick Start

The `i-am` plugin auto-registers the MCP server on install. The server starts automatically via stdio transport when Claude Code calls any memory tool -- no manual setup required.

Memory context is automatically injected into every agent's context via the `inject_memory.py` SubagentStart hook. Agents do NOT need to call `session_start()` or `recall()` to see memory data.

To run standalone (without the plugin):

```bash
cd memory-mcp
uv run python -m memory_mcp
```

## MCP Tools

18 tools registered on the `Memory` FastMCP server:

| Tool | Parameters | Description |
|------|-----------|-------------|
| `session_start` | *(none)* | Increment session counter, return memory summary with category counts |
| `remember` | `category`, `key`, `value`, `tags?`, `importance?`, `source_type?`, `confidence?`, `force?`, `broad?`, `summary?`, `type?`, `created_by?` | Store or update a memory entry with dedup-on-write. Auto-generates summary if not provided. `type` classifies the knowledge (decision, gotcha, pattern, convention, preference, correction, insight). `created_by` identifies the agent or user. |
| `forget` | `category`, `key` | **Soft-delete**: sets `invalid_at` timestamp and status to `superseded`. Entry remains queryable via `include_historical`. |
| `hard_delete` | `category`, `key` | **Permanent removal**: deletes entry and cleans incoming links. Creates backup. |
| `recall` | `category`, `key?` | Retrieve entries with access tracking |
| `search` | `query`, `category?`, `detail?`, `include_historical?`, `since?`, `type?` | Multi-signal ranked search. `detail="index"` returns Markdown summaries (default). `detail="full"` returns complete entries. `since` filters by creation time. `type` filters by knowledge type. |
| `browse_index` | `include_historical?` | Full memory index as Markdown-KV grouped by category. Most token-efficient view. |
| `consolidate` | `actions` (JSON), `dry_run?` | Execute structured actions (merge, archive, adjust_confidence, update_summary) atomically with backup. |
| `status` | *(none)* | Category counts, total entries, schema version, session count, file size |
| `export_memories` | `output_format?` | Export all memories as markdown (default) or JSON |
| `about_me` | *(none)* | Aggregated user profile from user, relationships, and tools categories |
| `about_us` | *(none)* | Aggregated user-assistant relationship profile |
| `reflect` | *(none)* | Lifecycle analysis: stale entries, archival candidates, confidence adjustments (read-only) |
| `connections` | `category`, `key` | Show outgoing and incoming links for an entry |
| `add_link` | `source_category`, `source_key`, `target_category`, `target_key`, `relation` | Create a unidirectional link between entries |
| `remove_link` | `source_category`, `source_key`, `target_category`, `target_key` | Remove a link between entries |
| `timeline` | `since?`, `until?`, `session_id?`, `tool_filter?`, `classification?`, `limit?` | Chronological observation history as compact Markdown. Groups events by date. Filter by date range, session, tool, or classification. |
| `session_narrative` | `session_id?` | Structured session summary: what was done, files touched, decisions made, outcome. Uses most recent session if omitted. |

## MCP Resources

| URI | Description |
|-----|-------------|
| `memory://schema` | Schema version, categories, statuses, relations, field documentation |
| `memory://stats` | Category counts, total entries, session count, file size |

## Schema

**Version**: 2.0

**Categories**: `user`, `assistant`, `project`, `relationships`, `tools`, `learnings`

Each memory entry contains:

| Field | Type | Description |
|-------|------|-------------|
| `value` | string | The memory content |
| `summary` | string | One-line description (~100 chars) for index browsing |
| `created_at` | ISO 8601 | Creation timestamp (UTC) |
| `updated_at` | ISO 8601 | Last modification timestamp (UTC) |
| `valid_at` | ISO 8601 | When entry became valid (set on creation) |
| `invalid_at` | ISO 8601 / null | When entry was soft-deleted (null if active) |
| `tags` | string[] | Tags for categorization and search |
| `importance` | int (1-10) | Priority level, default 5 |
| `confidence` | float (0.0-1.0) | Certainty level, null if unset |
| `source` | `{type, detail, agent_type, agent_id, session_id}` | Origin metadata with full provenance |
| `access_count` | int | Times recalled or searched |
| `last_accessed` | ISO 8601 / null | Last access timestamp |
| `status` | string | `active`, `archived`, or `superseded` |
| `links` | array | `[{target: "category.key", relation: "..."}]` |
| `type` | string / null | Knowledge type: `decision`, `gotcha`, `pattern`, `convention`, `preference`, `correction`, `insight` |
| `created_by` | string / null | Identifier for the agent or user that created the entry |

**Valid relations**: `supersedes`, `elaborates`, `contradicts`, `related-to`, `depends-on`

**Valid types**: `decision`, `gotcha`, `pattern`, `convention`, `preference`, `correction`, `insight`

## Key Features

**Progressive disclosure**: `browse_index()` returns a compact Markdown-KV summary of all entries (~400 tokens for 20 entries). `search(detail="index")` returns ranked Markdown summaries. Full entries available on demand via `detail="full"`. The calling LLM provides semantic search by reading the summaries.

**Temporal supersession**: `forget()` soft-deletes (sets `invalid_at` timestamp) instead of removing entries. Historical queries via `include_historical=True`. `hard_delete()` for permanent removal when needed.

**Structured consolidation**: `consolidate()` accepts a JSON array of actions (merge, archive, adjust_confidence, update_summary) and executes them atomically with pre-mutation backup. Supports `dry_run` for preview.

**Three-layer enforcement**: Memory context is injected into every agent via hook (Layer 1: `inject_memory.py` with LOCK_SH reads, importance tiers, agent-type-aware routing, and MAX_INJECT_CHARS budget). An always-loaded rule guides when to call `remember()` (Layer 2: `memory-protocol.md`). A validation hook warns when agents write LEARNINGS.md without calling `remember()` (Layer 3: `validate_memory.py`). Capture hooks (`capture_memory.py`, `capture_session.py`) write tool and lifecycle events to the observation layer. A promotion hook (`promote_learnings.py`) warns before LEARNINGS.md cleanup.

**Dedup-on-write**: `remember` scans for overlapping entries before writing. Returns candidates with ADD/UPDATE/NOOP recommendation. Use `force=True` to bypass.

**Multi-term search**: Queries are tokenized into individual terms. An entry matches if any term matches any field (key, value, tags, summary).

**Access tracking**: `recall` and `search` increment `access_count` and update `last_accessed`. Drives lifecycle analysis and search ranking.

**Ranked search**: Results scored by text match (0.4), tag overlap (0.2), importance (0.25), and recency (0.15). Recency uses exponential decay with ~21-day half-life.

**Cross-reference links**: Unidirectional links with five relation types. Auto-created on `remember` when 2+ tags overlap.

**Atomic writes**: All mutations use write-to-temp + `os.replace()` with `fcntl.flock()`.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_FILE` | `.ai-state/memory.json` | Path to the JSON memory file |

**Dual-layer storage**: Curated memories in `memory.json` (JSON, explicit `remember()` calls) and automatic observations in `observations.jsonl` (JSONL, captured by hooks). The observation layer provides chronological timelines and session narratives without polluting curated memory.

## Module Layout

```
src/memory_mcp/
  schema.py          -- v2.0 schema, MemoryEntry/Source/Link/Observation dataclasses, VALID_TYPES
  store.py           -- core CRUD, file I/O, locking, browse, consolidation
  search.py          -- scoring, ranking, text matching, Markdown formatting
  dedup.py           -- candidate detection, recommendation, word extraction
  consolidation.py   -- action validation and atomic execution
  lifecycle.py       -- read-only health analysis (stale, archival, confidence)
  observations.py    -- ObservationStore: JSONL I/O, rotation, querying
  narrative.py       -- build_timeline(), build_session_narrative()
  server.py          -- FastMCP tool and resource registration (18 tools)
```

## Development

```bash
cd memory-mcp
uv run pytest -v        # 329 tests across 13 test files
uv run ruff check src/  # lint
uv run ruff format src/ # format
```

## Hooks

Six hooks integrate with Claude Code's event system:

| Hook | Event | Description |
|------|-------|-------------|
| `inject_memory.py` | SubagentStart | Injects Markdown-KV summary with LOCK_SH reads, importance tiers, agent-type-aware category routing, and MAX_INJECT_CHARS budget |
| `validate_memory.py` | SubagentStop | Warns when agents write LEARNINGS.md without calling `remember()` |
| `capture_memory.py` | PostToolUse | Captures tool events as JSONL observations (blocklisted noisy tools excluded) |
| `capture_session.py` | SessionStart, Stop, SubagentStart, SubagentStop | Captures lifecycle events as JSONL observations |
| `promote_learnings.py` | PreToolUse | Warns before LEARNINGS.md cleanup when unpromoted entries exist |
| `memory-protocol.md` | *(always-loaded rule)* | Guides when and how to call `remember()` with type guidance |
