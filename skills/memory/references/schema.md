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

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Semantic version of the schema format. Used for future migrations |
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
        "confidence": null
      }
    }
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `value` | string | Yes | The memory content. Plain text, no length limit but prefer concise entries |
| `created_at` | string | Yes | ISO 8601 UTC timestamp of initial creation |
| `updated_at` | string | Yes | ISO 8601 UTC timestamp of last modification |
| `tags` | string[] | No | Classification labels for filtering and search. Defaults to `[]` |
| `confidence` | number \| null | No | Certainty level 0.0-1.0 for assistant self-knowledge. `null` for factual entries |

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
| Category names | Exactly one of: `user`, `assistant`, `project`, `relationships`, `tools`, `learnings` |
| JSON formatting | 2-space indentation, trailing newline |

## Example Document

A complete example showing entries across all categories:

```json
{
  "schema_version": "1.0",
  "memories": {
    "user": {
      "username": {
        "value": "@fperezsorrosal",
        "created_at": "2026-02-09T14:00:00Z",
        "updated_at": "2026-02-09T14:00:00Z",
        "tags": ["personal", "identity"],
        "confidence": null
      },
      "email": {
        "value": "fperezsorrosal@gmail.com",
        "created_at": "2026-02-09T14:00:00Z",
        "updated_at": "2026-02-09T14:00:00Z",
        "tags": ["personal", "identity"],
        "confidence": null
      },
      "github_url": {
        "value": "https://github.com/francisco-perez-sorrosal",
        "created_at": "2026-02-09T14:00:00Z",
        "updated_at": "2026-02-09T14:00:00Z",
        "tags": ["personal", "identity"],
        "confidence": null
      }
    },
    "assistant": {
      "response_style": {
        "value": "Concise and direct. Add detail only for complexity, obscurity, or user request.",
        "created_at": "2026-02-09T14:00:00Z",
        "updated_at": "2026-02-09T14:00:00Z",
        "tags": ["communication", "effectiveness"],
        "confidence": 0.9
      }
    },
    "project": {
      "repo_name": {
        "value": "ai-assistants -- configuration repository for AI coding assistants",
        "created_at": "2026-02-09T14:00:00Z",
        "updated_at": "2026-02-09T14:00:00Z",
        "tags": ["identity"],
        "confidence": null
      }
    },
    "relationships": {
      "collaboration_style": {
        "value": "Pragmatic, direct, values bold incremental changes. Prefers proactive agent usage.",
        "created_at": "2026-02-09T14:00:00Z",
        "updated_at": "2026-02-09T14:00:00Z",
        "tags": ["user-facing", "collaboration"],
        "confidence": 0.85
      }
    },
    "tools": {
      "clipboard": {
        "value": "pbcopy / pbpaste for clipboard interaction",
        "created_at": "2026-02-09T14:00:00Z",
        "updated_at": "2026-02-09T14:00:00Z",
        "tags": ["user-preference", "cli"],
        "confidence": null
      }
    },
    "learnings": {
      "plugin_hooks_not_auto_fired": {
        "value": "Plugin hooks in .claude-plugin/ install to cache but Claude Code never invokes them. Define hooks in settings.json instead.",
        "created_at": "2026-02-09T14:00:00Z",
        "updated_at": "2026-02-09T14:00:00Z",
        "tags": ["gotcha", "claude-code"],
        "confidence": 0.95
      }
    }
  }
}
```

## Migration Notes

### Schema Version 1.0 (Current)

Initial schema. No migrations needed.

### Future Migration Protocol

When the schema version changes:

1. Read the current `schema_version` from the file
2. Apply migration transforms sequentially (1.0 -> 1.1 -> 2.0, etc.)
3. Update `schema_version` to the target version
4. Create a backup before migration: `memory.pre-migration-<old_version>.json`

Planned evolution paths:
- **1.1**: Add `source` field (where the memory was captured -- session ID, command, etc.)
- **2.0**: Add `expires_at` for time-limited memories, `links` for cross-referencing entries
