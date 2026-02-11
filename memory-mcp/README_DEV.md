# Memory MCP Server -- Developer Guide

Architecture and internals for contributors. Read [README.md](README.md) for usage documentation.

## Architecture

A pure stdio MCP server with JSON file persistence. No HTTP server, no database, no background threads. The `i-am` plugin starts the process via `uv run` and communicates over stdin/stdout.

**Why MCP over SKILL.md procedures**: The previous approach had the LLM execute JSON read/write procedures from a skill file. This was fragile (non-deterministic execution), excluded sub-agents (skills require activation), and lacked atomicity. The MCP server provides deterministic Python operations, universal agent access via plugin registration, atomic file writes, and testable code.

```
LLM / Sub-agent  -->  MCP tools (stdio)  -->  MemoryStore  -->  memory.json
                                                    |
                                              lifecycle.py (read-only analysis)
```

## Module Map

| File | Purpose |
|------|---------|
| `schema.py` | Dataclasses (`MemoryEntry`, `Source`, `Link`), constants (`VALID_CATEGORIES`, `VALID_RELATIONS`, `SCHEMA_VERSION`), migration functions |
| `store.py` | `MemoryStore` class: CRUD operations, dedup logic, access tracking, link management, ranked search, atomic file I/O with locking |
| `server.py` | FastMCP server instance, 12 `@mcp.tool()` definitions, 2 `@mcp.resource()` endpoints, lazy store initialization |
| `lifecycle.py` | `analyze()` function: staleness detection, archival candidates, confidence adjustment proposals. Pure analysis, never mutates data |
| `__main__.py` | Entry point: imports `mcp` from `server`, calls `mcp.run()` |

## Key Design Decisions

**JSON over SQLite**: The memory file is committed to git and reviewed by humans. SQLite would break `git diff` workflows and require an export step. At <200 entries, JSON scan performance is irrelevant.

**Unidirectional links with reverse lookup**: Links are stored only on the source entry. The `connections` tool scans all entries for incoming links. This avoids bidirectional consistency issues and simplifies `forget` cleanup. At <200 entries, full scan takes microseconds.

**Within-category dedup**: `remember` checks for duplicates in the target category only (by default). Cross-category duplicates are legitimate -- a `tools` entry about "uses pixi" differs from a `project` entry. The `broad=True` flag enables cross-category scan when needed.

**Atomic writes with file locking**: All mutations use `_read_modify_write()`: acquire `fcntl.flock()`, load JSON, apply mutator function, write to temp file, `os.replace()` to target, release lock. Prevents corruption from concurrent agent writes.

**Dedup returns candidates, never auto-merges**: When `remember` finds overlapping entries, it returns candidates with match reasons and a recommendation (ADD/UPDATE/NOOP). The caller decides. Use `force=True` to bypass.

**Reflect is read-only analysis**: The `reflect` tool calls `lifecycle.analyze()` which returns findings without modifying data. The caller acts on findings by calling `forget`, `remember`, or other tools.

## Schema Evolution

```
v1.0 (original)
  |  adds: importance, source, access_count, last_accessed, status, session_count
  v
v1.1
  |  adds: links (array of {target, relation})
  v
v1.2 (current)
```

Migrations are chained: a v1.0 file migrates through v1.1 to v1.2 in a single load. Each step creates a backup before applying changes. Migration functions in `schema.py` return new dicts (no input mutation).

## Testing

```bash
uv run pytest -v              # all tests
uv run pytest tests/test_store.py  # specific module
```

Test files and coverage:

| File | Covers |
|------|--------|
| `test_schema.py` | Dataclass round-trips, migration v1.0 to v1.1 to v1.2, chained migration |
| `test_store.py` | CRUD cycle, access tracking, atomic writes, auto-migration, session start, export, about_me/about_us |
| `test_dedup.py` | Tag overlap detection, value similarity, force bypass, broad scan, recommendation logic |
| `test_lifecycle.py` | Staleness flags, archival candidates, confidence adjustments, read-only verification |
| `test_search.py` | Multi-signal ranking, weight verification, match reasons, category filtering |
| `test_links.py` | Link CRUD, connections (outgoing + incoming), auto-linking on remember, link cleanup on forget, duplicate prevention |

All tests use `tmp_path` fixtures for isolated file I/O.

## How to Extend

**Adding a new tool**:

1. Add the tool method to `MemoryStore` in `store.py`
2. Add the `@mcp.tool()` wrapper in `server.py` that delegates to the store
3. Add tests in `tests/`

**Adding a new schema field**:

1. Add the field to `MemoryEntry` in `schema.py` with a default value
2. Create a migration function (`migrate_v1_2_to_v1_3`) that adds the field to existing entries
3. Chain the migration in `MemoryStore._auto_migrate_if_needed()` in `store.py`
4. Bump `SCHEMA_VERSION`
5. Update `schema_resource()` in `server.py` to document the new field
6. Update `skills/memory/references/schema.md`
