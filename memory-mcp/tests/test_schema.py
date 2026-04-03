"""Tests for schema dataclasses and v2.0 schema."""

from __future__ import annotations

import pytest

from memory_mcp.schema import (
    DEFAULT_IMPORTANCE,
    SCHEMA_VERSION,
    VALID_CATEGORIES,
    VALID_RELATIONS,
    VALID_SOURCE_TYPES,
    VALID_STATUSES,
    VALID_TYPES,
    Link,
    MemoryEntry,
    Observation,
    Source,
    generate_summary,
)

# -- Source round-trip ---------------------------------------------------------


class TestSource:
    def test_default_source_round_trip(self):
        source = Source()
        restored = Source.from_dict(source.to_dict())
        assert restored == source

    def test_source_with_detail_round_trip(self):
        source = Source(type="user-stated", detail="user told me directly")
        data = source.to_dict()
        restored = Source.from_dict(data)
        assert restored == source
        assert data == {
            "type": "user-stated",
            "detail": "user told me directly",
            "agent_type": None,
            "agent_id": None,
            "session_id": None,
        }

    def test_source_from_dict_defaults(self):
        source = Source.from_dict({})
        assert source.type == "session"
        assert source.detail is None


# -- MemoryEntry round-trip ----------------------------------------------------


class TestMemoryEntry:
    def test_minimal_entry_round_trip(self):
        entry = MemoryEntry(
            value="test value",
            created_at="2026-02-10T06:35:00Z",
            updated_at="2026-02-10T06:35:00Z",
        )
        data = entry.to_dict()
        restored = MemoryEntry.from_dict(data)
        assert restored.value == entry.value
        assert restored.created_at == entry.created_at
        assert restored.updated_at == entry.updated_at
        assert restored.tags == []
        assert restored.confidence is None
        assert restored.importance == DEFAULT_IMPORTANCE
        assert restored.source == Source()
        assert restored.access_count == 0
        assert restored.last_accessed is None
        assert restored.status == "active"
        assert restored.summary == ""
        assert restored.valid_at is None
        assert restored.invalid_at is None

    def test_full_entry_round_trip(self):
        entry = MemoryEntry(
            value="Francisco",
            created_at="2026-02-10T06:35:00Z",
            updated_at="2026-02-10T07:00:00Z",
            tags=["personal", "identity"],
            confidence=0.95,
            importance=8,
            source=Source(type="user-stated", detail="from CLAUDE.md"),
            access_count=3,
            last_accessed="2026-02-10T08:00:00Z",
            status="active",
            summary="Francisco",
            valid_at="2026-02-10T06:35:00Z",
            invalid_at=None,
        )
        data = entry.to_dict()
        restored = MemoryEntry.from_dict(data)
        assert restored.value == entry.value
        assert restored.tags == entry.tags
        assert restored.confidence == entry.confidence
        assert restored.importance == entry.importance
        assert restored.source == entry.source
        assert restored.access_count == entry.access_count
        assert restored.last_accessed == entry.last_accessed
        assert restored.status == entry.status
        assert restored.summary == entry.summary
        assert restored.valid_at == entry.valid_at
        assert restored.invalid_at == entry.invalid_at

    def test_round_trip_is_lossless(self):
        """Verify dict -> dataclass -> dict produces identical output."""
        original = {
            "value": "test",
            "created_at": "2026-02-10T06:35:00Z",
            "updated_at": "2026-02-10T06:35:00Z",
            "tags": ["a", "b"],
            "confidence": 0.5,
            "importance": 7,
            "source": {
                "type": "inferred",
                "detail": "pattern match",
                "agent_type": None,
                "agent_id": None,
                "session_id": None,
            },
            "access_count": 2,
            "last_accessed": "2026-02-10T07:00:00Z",
            "status": "archived",
            "links": [{"target": "user.name", "relation": "related-to"}],
            "summary": "test",
            "valid_at": "2026-02-10T06:35:00Z",
            "invalid_at": None,
            "type": None,
            "created_by": None,
        }
        entry = MemoryEntry.from_dict(original)
        result = entry.to_dict()
        assert result == original

    def test_tags_list_is_independent_copy(self):
        """Verify to_dict produces an independent tags list."""
        entry = MemoryEntry(
            value="test",
            created_at="2026-02-10T06:35:00Z",
            updated_at="2026-02-10T06:35:00Z",
            tags=["a"],
        )
        data = entry.to_dict()
        data["tags"].append("b")
        assert entry.tags == ["a"]

    def test_new_fields_default_values(self):
        """Verify summary, valid_at, invalid_at have correct defaults."""
        entry = MemoryEntry(
            value="test",
            created_at="2026-02-10T06:35:00Z",
            updated_at="2026-02-10T06:35:00Z",
        )
        assert entry.summary == ""
        assert entry.valid_at is None
        assert entry.invalid_at is None

    def test_from_dict_without_new_fields(self):
        """Entries missing new fields get defaults (backward compatibility)."""
        data = {
            "value": "old entry",
            "created_at": "2026-02-10T06:35:00Z",
            "updated_at": "2026-02-10T06:35:00Z",
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.summary == ""
        assert entry.valid_at is None
        assert entry.invalid_at is None


# -- Constants -----------------------------------------------------------------


class TestConstants:
    def test_schema_version(self):
        assert SCHEMA_VERSION == "2.0"

    def test_valid_categories(self):
        assert set(VALID_CATEGORIES) == {
            "user",
            "assistant",
            "project",
            "relationships",
            "tools",
            "learnings",
        }

    def test_valid_statuses(self):
        assert set(VALID_STATUSES) == {"active", "archived", "superseded"}

    def test_valid_source_types(self):
        assert set(VALID_SOURCE_TYPES) == {"session", "user-stated", "inferred", "codebase"}

    def test_valid_relations(self):
        assert set(VALID_RELATIONS) == {
            "supersedes",
            "elaborates",
            "contradicts",
            "related-to",
            "depends-on",
        }


# -- Link round-trip ----------------------------------------------------------


class TestLink:
    def test_link_round_trip(self):
        link = Link(target="user.name", relation="related-to")
        data = link.to_dict()
        restored = Link.from_dict(data)
        assert restored == link
        assert data == {"target": "user.name", "relation": "related-to"}

    def test_link_from_dict(self):
        data = {"target": "learnings.python_patterns", "relation": "elaborates"}
        link = Link.from_dict(data)
        assert link.target == "learnings.python_patterns"
        assert link.relation == "elaborates"

    def test_link_is_frozen(self):
        link = Link(target="user.name", relation="related-to")
        with pytest.raises(AttributeError):
            link.target = "other.key"  # type: ignore[misc]


# -- MemoryEntry with links ---------------------------------------------------


class TestMemoryEntryLinks:
    def test_entry_with_links_round_trip(self):
        entry = MemoryEntry(
            value="test value",
            created_at="2026-02-10T06:35:00Z",
            updated_at="2026-02-10T06:35:00Z",
            links=[
                Link(target="user.email", relation="related-to"),
                Link(target="project.stack", relation="elaborates"),
            ],
        )
        data = entry.to_dict()
        restored = MemoryEntry.from_dict(data)
        assert len(restored.links) == 2
        assert restored.links[0] == Link(target="user.email", relation="related-to")
        assert restored.links[1] == Link(target="project.stack", relation="elaborates")
        assert restored.to_dict() == data

    def test_entry_without_links_defaults_to_empty(self):
        entry = MemoryEntry(
            value="test",
            created_at="2026-02-10T06:35:00Z",
            updated_at="2026-02-10T06:35:00Z",
        )
        assert entry.links == []
        assert entry.to_dict()["links"] == []

    def test_entry_from_dict_without_links_field(self):
        """Entries from older data (no links field) get empty links."""
        data = {
            "value": "old entry",
            "created_at": "2026-02-10T06:35:00Z",
            "updated_at": "2026-02-10T06:35:00Z",
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.links == []


# -- generate_summary ---------------------------------------------------------


class TestGenerateSummary:
    def test_short_value_unchanged(self):
        """Values under max_len are returned as-is."""
        assert generate_summary("short value") == "short value"

    def test_exact_max_len_unchanged(self):
        value = "x" * 100
        assert generate_summary(value) == value

    def test_truncates_long_value_at_word_boundary(self):
        value = "word " * 25  # 125 chars
        result = generate_summary(value, max_len=50)
        assert result.endswith("...")
        assert len(result) <= 53  # 50 + "..."

    def test_truncated_does_not_split_words(self):
        value = "the quick brown fox jumps over the lazy dog " * 5
        result = generate_summary(value, max_len=30)
        # Should not end with a partial word before "..."
        without_ellipsis = result[:-3]
        assert not without_ellipsis[-1].isalpha() or without_ellipsis.endswith(
            without_ellipsis.split()[-1]
        )

    def test_empty_value(self):
        assert generate_summary("") == ""

    def test_single_long_word(self):
        """A single word longer than max_len gets truncated at max_len."""
        value = "a" * 150
        result = generate_summary(value, max_len=100)
        # No space found, so truncate at max_len directly
        assert result.endswith("...")

    def test_custom_max_len(self):
        result = generate_summary("hello world", max_len=5)
        assert result.endswith("...")
        assert len(result) <= 10  # generous bound


# -- v2.0 enriched Source -----------------------------------------------------


class TestSourceV2:
    def test_enriched_source_round_trip(self):
        source = Source(
            type="session",
            detail="from tool use",
            agent_type="implementer",
            agent_id="impl-001",
            session_id="sess-abc",
        )
        data = source.to_dict()
        restored = Source.from_dict(data)
        assert restored == source
        assert data["agent_type"] == "implementer"
        assert data["agent_id"] == "impl-001"
        assert data["session_id"] == "sess-abc"

    def test_source_from_dict_new_fields_default_to_none(self):
        source = Source.from_dict({"type": "session", "detail": None})
        assert source.agent_type is None
        assert source.agent_id is None
        assert source.session_id is None

    def test_source_is_frozen(self):
        source = Source(agent_type="implementer")
        with pytest.raises(AttributeError):
            source.agent_type = "other"  # type: ignore[misc]


# -- v2.0 MemoryEntry with type and created_by --------------------------------


class TestMemoryEntryV2:
    def test_entry_with_type_and_created_by_round_trip(self):
        entry = MemoryEntry(
            value="Use pytest fixtures",
            created_at="2026-04-01T00:00:00Z",
            updated_at="2026-04-01T00:00:00Z",
            type="pattern",
            created_by="implementer",
        )
        data = entry.to_dict()
        restored = MemoryEntry.from_dict(data)
        assert restored.type == "pattern"
        assert restored.created_by == "implementer"
        assert data["type"] == "pattern"
        assert data["created_by"] == "implementer"

    def test_entry_from_dict_v2_fields_default_to_none(self):
        data = {
            "value": "old entry without v2 fields",
            "created_at": "2026-02-10T06:35:00Z",
            "updated_at": "2026-02-10T06:35:00Z",
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.type is None
        assert entry.created_by is None

    def test_entry_defaults_include_v2_fields(self):
        entry = MemoryEntry(
            value="test",
            created_at="2026-02-10T06:35:00Z",
            updated_at="2026-02-10T06:35:00Z",
        )
        assert entry.type is None
        assert entry.created_by is None


# -- v2.0 VALID_TYPES constant ------------------------------------------------


class TestValidTypes:
    def test_valid_types_has_seven_values(self):
        assert len(VALID_TYPES) == 7

    def test_valid_types_contains_expected_values(self):
        assert set(VALID_TYPES) == {
            "decision",
            "gotcha",
            "pattern",
            "convention",
            "preference",
            "correction",
            "insight",
        }


# -- Observation round-trip ----------------------------------------------------


class TestObservation:
    def test_minimal_observation_round_trip(self):
        obs = Observation(
            timestamp="2026-04-01T10:00:00Z",
            session_id="sess-001",
            agent_type="implementer",
            agent_id="impl-001",
            project="praxion",
            event_type="tool_use",
        )
        data = obs.to_dict()
        restored = Observation.from_dict(data)
        assert restored.timestamp == obs.timestamp
        assert restored.session_id == obs.session_id
        assert restored.agent_type == obs.agent_type
        assert restored.agent_id == obs.agent_id
        assert restored.project == obs.project
        assert restored.event_type == obs.event_type
        assert restored.tool_name is None
        assert restored.file_paths == []
        assert restored.outcome is None
        assert restored.classification is None
        assert restored.metadata == {}

    def test_full_observation_round_trip(self):
        obs = Observation(
            timestamp="2026-04-01T10:00:00Z",
            session_id="sess-001",
            agent_type="implementer",
            agent_id="impl-001",
            project="praxion",
            event_type="tool_use",
            tool_name="Write",
            file_paths=["src/schema.py", "tests/test_schema.py"],
            outcome="success",
            classification="implementation",
            metadata={"lines_changed": 42},
        )
        data = obs.to_dict()
        restored = Observation.from_dict(data)
        assert restored == obs
        assert data["tool_name"] == "Write"
        assert data["file_paths"] == ["src/schema.py", "tests/test_schema.py"]
        assert data["outcome"] == "success"
        assert data["classification"] == "implementation"
        assert data["metadata"] == {"lines_changed": 42}

    def test_observation_file_paths_independent_copy(self):
        obs = Observation(
            timestamp="2026-04-01T10:00:00Z",
            session_id="sess-001",
            agent_type="implementer",
            agent_id="impl-001",
            project="praxion",
            event_type="tool_use",
            file_paths=["a.py"],
        )
        data = obs.to_dict()
        data["file_paths"].append("b.py")
        assert obs.file_paths == ["a.py"]

    def test_observation_from_dict_defaults(self):
        data = {
            "timestamp": "2026-04-01T10:00:00Z",
            "session_id": "sess-001",
            "agent_type": "implementer",
            "agent_id": "impl-001",
            "project": "praxion",
            "event_type": "session_start",
        }
        obs = Observation.from_dict(data)
        assert obs.tool_name is None
        assert obs.file_paths == []
        assert obs.outcome is None
        assert obs.classification is None
        assert obs.metadata == {}
