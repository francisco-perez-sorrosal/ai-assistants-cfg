"""Schema dataclasses and migration logic for memory-mcp."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

# -- Constants ----------------------------------------------------------------

SCHEMA_VERSION = "1.2"

VALID_CATEGORIES = ("user", "assistant", "project", "relationships", "tools", "learnings")

VALID_STATUSES = ("active", "archived", "superseded")

VALID_SOURCE_TYPES = ("session", "user-stated", "inferred", "codebase")

VALID_RELATIONS = ("supersedes", "elaborates", "contradicts", "related-to", "depends-on")

DEFAULT_IMPORTANCE = 5
MIN_IMPORTANCE = 1
MAX_IMPORTANCE = 10


# -- Dataclasses --------------------------------------------------------------


@dataclass(frozen=True)
class Source:
    """Origin metadata for a memory entry."""

    type: str = "session"
    detail: str | None = None

    def to_dict(self) -> dict:
        return {"type": self.type, "detail": self.detail}

    @classmethod
    def from_dict(cls, data: dict) -> Source:
        return cls(type=data.get("type", "session"), detail=data.get("detail"))


@dataclass(frozen=True)
class Link:
    """A unidirectional link from one memory entry to another."""

    target: str  # format: "category.key"
    relation: str  # one of VALID_RELATIONS

    def to_dict(self) -> dict:
        return {"target": self.target, "relation": self.relation}

    @classmethod
    def from_dict(cls, data: dict) -> Link:
        return cls(target=data["target"], relation=data["relation"])


@dataclass
class MemoryEntry:
    """A single memory entry with v1.2 schema fields."""

    value: str
    created_at: str
    updated_at: str
    tags: list[str] = field(default_factory=list)
    confidence: float | None = None
    importance: int = DEFAULT_IMPORTANCE
    source: Source = field(default_factory=Source)
    access_count: int = 0
    last_accessed: str | None = None
    status: str = "active"
    links: list[Link] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tags": list(self.tags),
            "confidence": self.confidence,
            "importance": self.importance,
            "source": self.source.to_dict(),
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "status": self.status,
            "links": [link.to_dict() for link in self.links],
        }

    @classmethod
    def from_dict(cls, data: dict) -> MemoryEntry:
        source_data = data.get("source", {"type": "session", "detail": None})
        links_data = data.get("links", [])
        return cls(
            value=data["value"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            tags=list(data.get("tags", [])),
            confidence=data.get("confidence"),
            importance=data.get("importance", DEFAULT_IMPORTANCE),
            source=Source.from_dict(source_data),
            access_count=data.get("access_count", 0),
            last_accessed=data.get("last_accessed"),
            status=data.get("status", "active"),
            links=[Link.from_dict(ld) for ld in links_data],
        )


# -- Migration ----------------------------------------------------------------


def migrate_v1_0_to_v1_1(data: dict) -> dict:
    """Migrate a v1.0 memory document to v1.1.

    Adds default values for new fields to every entry and bumps the schema version.
    Does NOT mutate the input dict -- returns a new dict.
    """
    result = copy.deepcopy(data)

    memories = result.get("memories", {})
    for _category_name, entries in memories.items():
        for _key, entry in entries.items():
            entry.setdefault("importance", DEFAULT_IMPORTANCE)
            entry.setdefault("source", {"type": "session", "detail": None})
            entry.setdefault("access_count", 0)
            entry.setdefault("last_accessed", None)
            entry.setdefault("status", "active")

    result.setdefault("session_count", 0)
    result["schema_version"] = "1.1"

    return result


def migrate_v1_1_to_v1_2(data: dict) -> dict:
    """Migrate a v1.1 memory document to v1.2.

    Adds empty ``links`` list to every entry and bumps the schema version.
    Does NOT mutate the input dict -- returns a new dict.
    """
    result = copy.deepcopy(data)

    memories = result.get("memories", {})
    for _category_name, entries in memories.items():
        for _key, entry in entries.items():
            entry.setdefault("links", [])

    result["schema_version"] = "1.2"

    return result
