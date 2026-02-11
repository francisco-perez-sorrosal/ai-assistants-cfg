"""MCP server definition, tool registration, and resource endpoints."""

from __future__ import annotations

import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from memory_mcp.schema import SCHEMA_VERSION, VALID_CATEGORIES, VALID_RELATIONS, VALID_STATUSES
from memory_mcp.store import MemoryStore

# -- Server instance ----------------------------------------------------------

mcp = FastMCP("Memory")

# -- Lazy store initialization ------------------------------------------------

DEFAULT_MEMORY_FILE = ".ai-state/memory.json"

_store: MemoryStore | None = None


def _get_store() -> MemoryStore:
    """Return the singleton MemoryStore, creating it on first call."""
    global _store  # noqa: PLW0603
    if _store is None:
        memory_file = os.environ.get("MEMORY_FILE", DEFAULT_MEMORY_FILE)
        _store = MemoryStore(Path(memory_file))
    return _store


# -- MCP Tools ----------------------------------------------------------------


@mcp.tool()
def session_start() -> dict:
    """Start or resume a memory session.

    Increments the session counter and returns a summary of all stored memories
    including category counts, total entries, and schema version.
    Call this at the beginning of each conversation.
    """
    try:
        return _get_store().session_start()
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def remember(
    category: str,
    key: str,
    value: str,
    tags: list[str] | None = None,
    importance: int = 5,
    source_type: str = "session",
    confidence: float | None = None,
    force: bool = False,
    broad: bool = False,
) -> dict:
    """Store a new memory or update an existing one.

    Creates or updates a memory entry in the specified category.
    If the key already exists, its value is updated and tags are merged.

    For new keys, checks for similar existing entries first. If candidates
    are found, returns them with a recommendation instead of writing.
    Call again with force=True to bypass the check, or use the existing
    key to update the matched entry.

    Args:
        category: One of: user, assistant, project, relationships, tools, learnings.
        key: Unique identifier within the category (e.g., "preferred-language").
        value: The memory content to store.
        tags: Optional list of tags for categorization and search.
        importance: Priority from 1 (low) to 10 (critical). Default 5.
        source_type: Origin: "session", "user-stated", "inferred", or "codebase".
        confidence: Optional confidence score (0.0 to 1.0).
        force: If True, skip deduplication check and write immediately.
        broad: If True, check for duplicates across all categories (not just target).
    """
    try:
        return _get_store().remember(
            category,
            key,
            value,
            tags=tags,
            importance=importance,
            source_type=source_type,
            confidence=confidence,
            force=force,
            broad=broad,
        )
    except (ValueError, KeyError) as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": f"Unexpected error: {exc}"}


@mcp.tool()
def forget(category: str, key: str) -> dict:
    """Remove a memory entry.

    Deletes the specified entry and creates a backup of the full store
    before removal. Returns the removed entry data and backup path.

    Args:
        category: The category containing the entry.
        key: The key of the entry to remove.
    """
    try:
        return _get_store().forget(category, key)
    except (ValueError, KeyError) as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": f"Unexpected error: {exc}"}


@mcp.tool()
def recall(category: str, key: str | None = None) -> dict:
    """Retrieve stored memories with access tracking.

    Returns entries from a category, optionally filtered by key.
    Each recalled entry has its access count incremented and last-accessed
    timestamp updated.

    Args:
        category: The category to recall from.
        key: Optional specific key. If omitted, returns all entries in the category.
    """
    try:
        return _get_store().recall(category, key)
    except (ValueError, KeyError) as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": f"Unexpected error: {exc}"}


@mcp.tool()
def search(query: str, category: str | None = None) -> dict:
    """Search memories by text across keys, values, and tags.

    Case-insensitive search with match reasons indicating where each
    result matched (key, value, or tag). Results have their access
    counts updated.

    Args:
        query: Search text to match against entries.
        category: Optional category filter. If omitted, searches all categories.
    """
    try:
        return _get_store().search(query, category)
    except ValueError as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": f"Unexpected error: {exc}"}


@mcp.tool()
def status() -> dict:
    """Return memory store status.

    Shows category counts, total entries, schema version, session count,
    and file size. Use this for a quick health check.
    """
    try:
        return _get_store().status()
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def export_memories(output_format: str = "markdown") -> dict:
    """Export all memories as markdown or JSON.

    Args:
        output_format: Export format -- "markdown" (default) or "json".
    """
    try:
        return _get_store().export(output_format)
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def about_me() -> dict:
    """Get a profile summary of the user.

    Aggregates entries from user, relationships (user-facing tagged),
    and tools (user-preference tagged) categories into a readable profile.
    """
    try:
        return _get_store().about_me()
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def about_us() -> dict:
    """Get a summary of the user-assistant relationship.

    Aggregates relationship entries and assistant identity entries
    into a readable relationship profile.
    """
    try:
        return _get_store().about_us()
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def reflect() -> dict:
    """Analyze memory health and suggest lifecycle actions.

    Returns a structured analysis of the memory store including:
    - Stale entries (never accessed, created 7+ days ago)
    - Archival candidates (low importance, never accessed, still active)
    - Proposed confidence adjustments based on access patterns and source type

    Read-only -- does not modify any entries. Use the results to decide
    which entries to archive, update, or remove.
    """
    try:
        return _get_store().reflect()
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def connections(category: str, key: str) -> dict:
    """Show all links to and from a memory entry.

    Returns outgoing links (from this entry to others) and incoming links
    (from other entries pointing to this one). Each link includes the
    target/source reference, relation type, and a summary of the linked entry.

    Args:
        category: The category of the entry.
        key: The key of the entry.
    """
    try:
        return _get_store().connections(category, key)
    except (ValueError, KeyError) as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": f"Unexpected error: {exc}"}


@mcp.tool()
def add_link(
    source_category: str,
    source_key: str,
    target_category: str,
    target_key: str,
    relation: str,
) -> dict:
    """Create a unidirectional link between two memory entries.

    Links express semantic relationships between entries. The link is stored
    on the source entry and points to the target.

    Args:
        source_category: Category of the source entry.
        source_key: Key of the source entry.
        target_category: Category of the target entry.
        target_key: Key of the target entry.
        relation: One of: supersedes, elaborates, contradicts, related-to, depends-on.
    """
    try:
        return _get_store().add_link(
            source_category, source_key, target_category, target_key, relation
        )
    except (ValueError, KeyError) as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": f"Unexpected error: {exc}"}


@mcp.tool()
def remove_link(
    source_category: str,
    source_key: str,
    target_category: str,
    target_key: str,
) -> dict:
    """Remove a link between two memory entries.

    Removes all links from the source entry that point to the target entry,
    regardless of relation type.

    Args:
        source_category: Category of the source entry.
        source_key: Key of the source entry.
        target_category: Category of the target entry.
        target_key: Key of the target entry.
    """
    try:
        return _get_store().remove_link(
            source_category, source_key, target_category, target_key
        )
    except (ValueError, KeyError) as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": f"Unexpected error: {exc}"}


# -- MCP Resources ------------------------------------------------------------


@mcp.resource("memory://schema")
def schema_resource() -> str:
    """Memory schema version and field documentation.

    Returns the current schema version, valid categories, statuses,
    and a description of each field in a memory entry.
    """
    schema_info = {
        "schema_version": SCHEMA_VERSION,
        "categories": list(VALID_CATEGORIES),
        "statuses": list(VALID_STATUSES),
        "entry_fields": {
            "value": "The memory content (string, required)",
            "created_at": "ISO 8601 UTC timestamp when the entry was created",
            "updated_at": "ISO 8601 UTC timestamp of the last modification",
            "tags": "List of string tags for categorization and search",
            "confidence": "Confidence score from 0.0 to 1.0 (null if unset)",
            "importance": "Priority from 1 (low) to 10 (critical), default 5",
            "source": "Origin metadata: {type, detail}",
            "access_count": "Number of times this entry has been recalled/searched",
            "last_accessed": "ISO 8601 UTC timestamp of last access (null if never)",
            "status": "Entry lifecycle: active, archived, or superseded",
            "links": "Array of {target, relation} linking to other entries",
        },
        "valid_relations": list(VALID_RELATIONS),
    }
    return json.dumps(schema_info, indent=2)


@mcp.resource("memory://stats")
def stats_resource() -> str:
    """Memory store statistics.

    Returns category counts, total entries, session count,
    and last modified timestamp.
    """
    try:
        store = _get_store()
        store_status = store.status()
        stats = {
            "categories": store_status["categories"],
            "total": store_status["total"],
            "session_count": store_status["session_count"],
            "schema_version": store_status["schema_version"],
            "file_size": store_status["file_size"],
        }
        return json.dumps(stats, indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc)})
