"""Schema dataclasses for memory-mcp v2.0."""

from __future__ import annotations

from dataclasses import dataclass, field

# -- Constants ----------------------------------------------------------------

SCHEMA_VERSION = "2.0"

VALID_CATEGORIES = ("user", "assistant", "project", "relationships", "tools", "learnings")

VALID_TYPES = (
    "decision",
    "gotcha",
    "pattern",
    "convention",
    "preference",
    "correction",
    "insight",
)

VALID_STATUSES = ("active", "archived", "superseded")

VALID_SOURCE_TYPES = ("session", "user-stated", "inferred", "codebase")

VALID_RELATIONS = ("supersedes", "elaborates", "contradicts", "related-to", "depends-on")

DEFAULT_IMPORTANCE = 5
MIN_IMPORTANCE = 1
MAX_IMPORTANCE = 10

SUMMARY_MAX_LENGTH = 100


# -- Summary generation -------------------------------------------------------


def generate_summary(value: str, max_len: int = SUMMARY_MAX_LENGTH) -> str:
    """Generate a one-line summary from a value string.

    Truncates at a word boundary and appends "..." if the value exceeds max_len.
    """
    if len(value) <= max_len:
        return value

    # Find the last space before max_len to avoid splitting a word
    truncated = value[:max_len]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]

    return truncated.rstrip() + "..."


# -- Dataclasses --------------------------------------------------------------


@dataclass(frozen=True)
class Source:
    """Origin metadata for a memory entry."""

    type: str = "session"
    detail: str | None = None
    agent_type: str | None = None
    agent_id: str | None = None
    session_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "detail": self.detail,
            "agent_type": self.agent_type,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Source:
        return cls(
            type=data.get("type", "session"),
            detail=data.get("detail"),
            agent_type=data.get("agent_type"),
            agent_id=data.get("agent_id"),
            session_id=data.get("session_id"),
        )


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
    """A single memory entry with v2.0 schema fields."""

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
    summary: str = ""
    valid_at: str | None = None
    invalid_at: str | None = None
    type: str | None = None
    created_by: str | None = None

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
            "summary": self.summary,
            "valid_at": self.valid_at,
            "invalid_at": self.invalid_at,
            "type": self.type,
            "created_by": self.created_by,
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
            summary=data.get("summary", ""),
            valid_at=data.get("valid_at"),
            invalid_at=data.get("invalid_at"),
            type=data.get("type"),
            created_by=data.get("created_by"),
        )


# -- Observation (JSONL layer) ------------------------------------------------

VALID_EVENT_TYPES = (
    "tool_use",
    "session_start",
    "session_stop",
    "agent_start",
    "agent_stop",
)


@dataclass
class Observation:
    """A single observation event for the JSONL observation layer."""

    timestamp: str
    session_id: str
    agent_type: str
    agent_id: str
    project: str
    event_type: str  # one of VALID_EVENT_TYPES
    tool_name: str | None = None
    file_paths: list[str] = field(default_factory=list)
    outcome: str | None = None  # success, failure
    classification: str | None = None  # decision, test, commit, implementation, etc.
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "agent_type": self.agent_type,
            "agent_id": self.agent_id,
            "project": self.project,
            "event_type": self.event_type,
            "tool_name": self.tool_name,
            "file_paths": list(self.file_paths),
            "outcome": self.outcome,
            "classification": self.classification,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Observation:
        return cls(
            timestamp=data["timestamp"],
            session_id=data["session_id"],
            agent_type=data["agent_type"],
            agent_id=data["agent_id"],
            project=data["project"],
            event_type=data["event_type"],
            tool_name=data.get("tool_name"),
            file_paths=list(data.get("file_paths", [])),
            outcome=data.get("outcome"),
            classification=data.get("classification"),
            metadata=dict(data.get("metadata", {})),
        )
