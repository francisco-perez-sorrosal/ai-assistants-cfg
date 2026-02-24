# Memory JSON Schema

Full schema reference for `.ai-state/memory.json`. Loaded on-demand from the memory skill.

## Table of Contents

- [Top-Level Structure](#top-level-structure)
- [Memory Entry Schema](#memory-entry-schema)
- [Category Definitions](#category-definitions)
- [Field Constraints](#field-constraints)
- [Example Document](#example-document)
- [Migration Notes](#migration-notes)

## Top-Level Structure

```json
{
  "schema_version": "1.2",
  "session_count": 0,
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

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Semantic version of the schema format. Current: `"1.2"` |
| `session_count` | integer | Number of sessions started via `session_start`. Default `0`. Added in v1.1 |
| `memories` | object | Container with one key per category. Each category maps string keys to entry objects |

## Memory Entry Schema

Each entry is stored as a key-value pair inside its category object:

```json
{
  "memories": {
    "user": {
      "username": {
        "value": "@fperezsorrosal",
        "created_at": "2026-02-09T14:00:00Z",
        "updated_at": "2026-02-09T14:00:00Z",
        "tags": ["personal", "identity"],
        "confidence": null,
        "importance": 8,
        "source": { "type": "user-stated", "detail": null },
        "access_count": 3,
        "last_accessed": "2026-02-10T10:00:00Z",
        "status": "active",
        "links": [
          { "target": "user.email", "relation": "related-to" }
        ]
      }
    }
  }
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `value` | string | Yes | -- | The memory content. Plain text, prefer concise entries |
| `created_at` | string | Yes | -- | ISO 8601 UTC timestamp of initial creation |
| `updated_at` | string | Yes | -- | ISO 8601 UTC timestamp of last modification |
| `tags` | string[] | No | `[]` | Classification labels for filtering and search |
| `confidence` | number \| null | No | `null` | Certainty level 0.0-1.0 for assistant self-knowledge. `null` for factual entries |
| `importance` | integer | No | `5` | Priority from 1 (low) to 10 (critical). Added in v1.1 |
| `source` | object | No | `{"type": "session", "detail": null}` | Origin metadata. Added in v1.1 |
| `source.type` | string | Yes | `"session"` | One of: `"session"`, `"user-stated"`, `"inferred"`, `"codebase"` |
| `source.detail` | string \| null | No | `null` | Additional context about the source (e.g., command name, file path) |
| `access_count` | integer | No | `0` | Number of times recalled or found via search. Added in v1.1 |
| `last_accessed` | string \| null | No | `null` | ISO 8601 UTC timestamp of last recall/search access. `null` if never accessed. Added in v1.1 |
| `status` | string | No | `"active"` | Entry lifecycle state. One of: `"active"`, `"archived"`, `"superseded"`. Added in v1.1 |
| `links` | object[] | No | `[]` | Array of unidirectional links to other entries. Added in v1.2 |
| `links[].target` | string | Yes | -- | Reference to the linked entry in `"category.key"` format |
| `links[].relation` | string | Yes | -- | One of: `"supersedes"`, `"elaborates"`, `"contradicts"`, `"related-to"`, `"depends-on"` |

## Category Definitions

### user

Personal information, preferences, and habits about the human user.

**Typical keys**: `first_name`, `last_name`, `username` (alias), `email`, `github_url`, `response_style_preference`, `workflow_habits`, `communication_style`, `timezone`, `preferred_languages`

**Tags**: `personal`, `identity`, `alias`, `preference`, `workflow`, `communication`

**Confidence**: Always `null` -- user facts are authoritative, not probabilistic.

### assistant

Self-identity and self-knowledge the assistant accumulates about its own patterns, effective approaches, and mistakes.

**Typical keys**: `name` (required -- auto-assigned if missing), `response_style`, `effective_approaches`, `common_mistakes`, `user_correction_patterns`, `model_limitations`

**Tags**: `identity`, `self-awareness`, `effectiveness`, `correction`, `limitation`

**Confidence**: 0.0-1.0 recommended. Low confidence (< 0.5) for new observations, high confidence (> 0.8) for confirmed patterns.

### project

Project-specific conventions, architecture decisions, and technical choices.

**Typical keys**: `tech_stack`, `architecture_pattern`, `naming_convention`, `deployment_target`, `testing_approach`, `dependency_management`

**Tags**: `convention`, `architecture`, `tooling`, `decision`, `constraint`

**Confidence**: `null` for documented decisions, 0.0-1.0 for inferred patterns.

### relationships

How the user and assistant interact -- delegation style, trust levels, collaboration patterns.

**Typical keys**: `delegation_style`, `trust_level`, `feedback_style`, `preferred_autonomy`, `communication_cadence`, `conflict_resolution`

**Tags**: `user-facing`, `collaboration`, `trust`, `feedback`, `autonomy`

**Confidence**: 0.0-1.0 recommended. Relationship patterns emerge over time.

### tools

Tool preferences, environment configuration, CLI shortcuts, and setup details.

**Typical keys**: `package_manager`, `editor`, `shell`, `clipboard_tool`, `version_control`, `ci_cd`, `container_runtime`

**Tags**: `user-preference`, `environment`, `cli`, `configuration`, `automation`

**Confidence**: `null` for explicit preferences, 0.0-1.0 for inferred.

### learnings

Cross-session insights, gotchas, discovered patterns, and debugging solutions.

**Typical keys**: Descriptive slugs like `hook_payload_field_names`, `plugin_cache_path_changes`, `pixi_lock_file_handling`

**Tags**: `gotcha`, `debugging`, `pattern`, `workaround`, `insight`, `performance`

**Confidence**: 0.0-1.0 recommended. Higher for repeatedly confirmed insights.

## Field Constraints

| Constraint | Rule |
|------------|------|
| Key format | Lowercase, underscores for word separation. No spaces, no special characters beyond `_` and `-` |
| Key uniqueness | Keys must be unique within a category. Cross-category duplicates are allowed |
| Value length | No hard limit, but prefer entries under 500 characters. Use multiple related entries for complex knowledge |
| Timestamp format | ISO 8601 with UTC timezone: `YYYY-MM-DDTHH:MM:SSZ` |
| Tags | Lowercase, hyphen-separated. No spaces. Each tag under 50 characters |
| Confidence range | `null` or a float between 0.0 and 1.0 inclusive |
| Importance range | Integer between 1 and 10 inclusive. Default 5 |
| Source types | One of: `"session"`, `"user-stated"`, `"inferred"`, `"codebase"` |
| Status values | One of: `"active"`, `"archived"`, `"superseded"` |
| Link relations | One of: `"supersedes"`, `"elaborates"`, `"contradicts"`, `"related-to"`, `"depends-on"` |
| Link target format | `"category.key"` referencing an existing entry |
| Category names | Exactly one of: `user`, `assistant`, `project`, `relationships`, `tools`, `learnings` |
| JSON formatting | 2-space indentation, trailing newline |

## Example Document

A complete v1.2 example showing entries across all categories:

```json
{
  "schema_version": "1.2",
  "session_count": 12,
  "memories": {
    "user": {
      "username": {
        "value": "@fperezsorrosal",
        "created_at": "2026-02-09T14:00:00Z",
        "updated_at": "2026-02-09T14:00:00Z",
        "tags": ["personal", "identity"],
        "confidence": null,
        "importance": 8,
        "source": { "type": "user-stated", "detail": null },
        "access_count": 5,
        "last_accessed": "2026-02-10T16:30:00Z",
        "status": "active",
        "links": [
          { "target": "user.email", "relation": "related-to" },
          { "target": "user.github_url", "relation": "related-to" }
        ]
      },
      "email": {
        "value": "fperezsorrosal@gmail.com",
        "created_at": "2026-02-09T14:00:00Z",
        "updated_at": "2026-02-09T14:00:00Z",
        "tags": ["personal", "identity"],
        "confidence": null,
        "importance": 7,
        "source": { "type": "user-stated", "detail": null },
        "access_count": 2,
        "last_accessed": "2026-02-10T12:00:00Z",
        "status": "active",
        "links": []
      },
      "github_url": {
        "value": "https://github.com/francisco-perez-sorrosal",
        "created_at": "2026-02-09T14:00:00Z",
        "updated_at": "2026-02-09T14:00:00Z",
        "tags": ["personal", "identity"],
        "confidence": null,
        "importance": 6,
        "source": { "type": "user-stated", "detail": null },
        "access_count": 1,
        "last_accessed": "2026-02-10T10:00:00Z",
        "status": "active",
        "links": []
      }
    },
    "assistant": {
      "response_style": {
        "value": "Concise and direct. Add detail only for complexity, obscurity, or user request.",
        "created_at": "2026-02-09T14:00:00Z",
        "updated_at": "2026-02-09T14:00:00Z",
        "tags": ["communication", "effectiveness"],
        "confidence": 0.9,
        "importance": 7,
        "source": { "type": "inferred", "detail": null },
        "access_count": 8,
        "last_accessed": "2026-02-10T18:00:00Z",
        "status": "active",
        "links": []
      }
    },
    "project": {
      "repo_name": {
        "value": "ai-assistants -- configuration repository for AI coding assistants",
        "created_at": "2026-02-09T14:00:00Z",
        "updated_at": "2026-02-09T14:00:00Z",
        "tags": ["identity"],
        "confidence": null,
        "importance": 5,
        "source": { "type": "codebase", "detail": null },
        "access_count": 3,
        "last_accessed": "2026-02-10T14:00:00Z",
        "status": "active",
        "links": []
      }
    },
    "relationships": {
      "collaboration_style": {
        "value": "Pragmatic, direct, values purposeful incremental evolution. Prefers proactive agent usage.",
        "created_at": "2026-02-09T14:00:00Z",
        "updated_at": "2026-02-09T14:00:00Z",
        "tags": ["user-facing", "collaboration"],
        "confidence": 0.85,
        "importance": 6,
        "source": { "type": "inferred", "detail": null },
        "access_count": 4,
        "last_accessed": "2026-02-10T15:00:00Z",
        "status": "active",
        "links": []
      }
    },
    "tools": {
      "clipboard": {
        "value": "pbcopy / pbpaste for clipboard interaction",
        "created_at": "2026-02-09T14:00:00Z",
        "updated_at": "2026-02-09T14:00:00Z",
        "tags": ["user-preference", "cli"],
        "confidence": null,
        "importance": 4,
        "source": { "type": "user-stated", "detail": null },
        "access_count": 0,
        "last_accessed": null,
        "status": "active",
        "links": []
      }
    },
    "learnings": {
      "plugin_hooks_not_auto_fired": {
        "value": "Plugin hooks in .claude-plugin/ install to cache but Claude Code never invokes them. Define hooks in settings.json instead.",
        "created_at": "2026-02-09T14:00:00Z",
        "updated_at": "2026-02-09T14:00:00Z",
        "tags": ["gotcha", "claude-code"],
        "confidence": 0.95,
        "importance": 8,
        "source": { "type": "session", "detail": null },
        "access_count": 2,
        "last_accessed": "2026-02-10T11:00:00Z",
        "status": "active",
        "links": []
      }
    }
  }
}
```

## Migration Notes

### Schema Version 1.2 (Current)

Added cross-referencing links between entries. Enables connection discovery via the `connections`, `add_link`, and `remove_link` tools.

**New entry field**: `links`

### v1.1 to v1.2 Migration

Applied automatically by the MCP server on first load of a v1.1 document. A backup is created at `.ai-state/memory.pre-migration-1.1.json` before migration.

| Field | Default Value |
|-------|---------------|
| `links` | `[]` |

All v1.1 fields are preserved unchanged.

### Link Relations

| Relation | Usage |
|----------|-------|
| `supersedes` | This entry replaces the target (target should be archived) |
| `elaborates` | This entry provides more detail about the target |
| `contradicts` | This entry conflicts with the target (needs resolution) |
| `related-to` | General association (auto-created when entries share 2+ tags) |
| `depends-on` | This entry's validity depends on the target |

### Schema Version 1.1

Added lifecycle and provenance tracking fields. All v1.0 data is preserved; new fields receive sensible defaults during migration.

**New entry fields**: `importance`, `source`, `access_count`, `last_accessed`, `status`

**New top-level field**: `session_count`

### v1.0 to v1.1 Migration

Applied automatically by the MCP server on first load of a v1.0 document. A backup is created at `.ai-state/memory.pre-migration-1.0.json` before migration.

| Field | Default Value |
|-------|---------------|
| `importance` | `5` |
| `source` | `{"type": "session", "detail": null}` |
| `access_count` | `0` |
| `last_accessed` | `null` |
| `status` | `"active"` |
| `session_count` (top-level) | `0` |

All original v1.0 fields (`value`, `created_at`, `updated_at`, `tags`, `confidence`) are preserved unchanged.

### Schema Version 1.0

Initial schema. Five entry fields: `value`, `created_at`, `updated_at`, `tags`, `confidence`. No top-level `session_count`.

### Migration Protocol

When the schema version changes:

1. Read the current `schema_version` from the file
2. Apply migration transforms sequentially (1.0 -> 1.1 -> 1.2)
3. Update `schema_version` to the target version
4. Create a backup before each migration step: `memory.pre-migration-<old_version>.json`
