"""Tests for schema dataclasses and migration logic."""

from __future__ import annotations

import copy

from memory_mcp.schema import (
    DEFAULT_IMPORTANCE,
    SCHEMA_VERSION,
    VALID_CATEGORIES,
    VALID_RELATIONS,
    VALID_SOURCE_TYPES,
    VALID_STATUSES,
    Link,
    MemoryEntry,
    Source,
    migrate_v1_0_to_v1_1,
    migrate_v1_1_to_v1_2,
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
        assert data == {"type": "user-stated", "detail": "user told me directly"}

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

    def test_round_trip_is_lossless(self):
        """Verify dict -> dataclass -> dict produces identical output."""
        original = {
            "value": "test",
            "created_at": "2026-02-10T06:35:00Z",
            "updated_at": "2026-02-10T06:35:00Z",
            "tags": ["a", "b"],
            "confidence": 0.5,
            "importance": 7,
            "source": {"type": "inferred", "detail": "pattern match"},
            "access_count": 2,
            "last_accessed": "2026-02-10T07:00:00Z",
            "status": "archived",
            "links": [{"target": "user.name", "relation": "related-to"}],
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


# -- Constants -----------------------------------------------------------------


class TestConstants:
    def test_schema_version(self):
        assert SCHEMA_VERSION == "1.2"

    def test_valid_categories(self):
        assert set(VALID_CATEGORIES) == {
            "user", "assistant", "project", "relationships", "tools", "learnings"
        }

    def test_valid_statuses(self):
        assert set(VALID_STATUSES) == {"active", "archived", "superseded"}

    def test_valid_source_types(self):
        assert set(VALID_SOURCE_TYPES) == {"session", "user-stated", "inferred", "codebase"}

    def test_valid_relations(self):
        assert set(VALID_RELATIONS) == {
            "supersedes", "elaborates", "contradicts", "related-to", "depends-on"
        }


# -- Migration v1.0 -> v1.1 ---------------------------------------------------


def _make_v1_0_document() -> dict:
    """Create a v1.0 document matching the live memory.json structure."""
    return {
        "schema_version": "1.0",
        "memories": {
            "user": {
                "first_name": {
                    "value": "Francisco",
                    "created_at": "2026-02-10T06:35:00Z",
                    "updated_at": "2026-02-10T06:35:00Z",
                    "tags": ["personal", "identity"],
                    "confidence": None,
                },
                "coding_philosophy": {
                    "value": "Pragmatism is non-negotiable.",
                    "created_at": "2026-02-10T06:35:00Z",
                    "updated_at": "2026-02-10T06:35:00Z",
                    "tags": ["preference", "philosophy"],
                    "confidence": None,
                },
            },
            "assistant": {
                "name": {
                    "value": "Kael",
                    "created_at": "2026-02-09T00:00:00Z",
                    "updated_at": "2026-02-09T00:00:00Z",
                    "tags": ["identity"],
                    "confidence": None,
                },
            },
            "relationships": {
                "collaboration_style": {
                    "value": "Pragmatic, direct.",
                    "created_at": "2026-02-10T06:35:00Z",
                    "updated_at": "2026-02-10T06:35:00Z",
                    "tags": ["user-facing", "collaboration"],
                    "confidence": 0.85,
                },
            },
        },
    }


class TestMigration:
    def test_bumps_schema_version(self):
        v1_0 = _make_v1_0_document()
        v1_1 = migrate_v1_0_to_v1_1(v1_0)
        assert v1_1["schema_version"] == "1.1"

    def test_adds_session_count(self):
        v1_0 = _make_v1_0_document()
        v1_1 = migrate_v1_0_to_v1_1(v1_0)
        assert v1_1["session_count"] == 0

    def test_adds_new_fields_with_defaults(self):
        v1_0 = _make_v1_0_document()
        v1_1 = migrate_v1_0_to_v1_1(v1_0)

        entry = v1_1["memories"]["user"]["first_name"]
        assert entry["importance"] == DEFAULT_IMPORTANCE
        assert entry["source"] == {"type": "session", "detail": None}
        assert entry["access_count"] == 0
        assert entry["last_accessed"] is None
        assert entry["status"] == "active"

    def test_preserves_original_data(self):
        v1_0 = _make_v1_0_document()
        v1_1 = migrate_v1_0_to_v1_1(v1_0)

        # Original v1.0 fields preserved
        entry = v1_1["memories"]["user"]["first_name"]
        assert entry["value"] == "Francisco"
        assert entry["created_at"] == "2026-02-10T06:35:00Z"
        assert entry["updated_at"] == "2026-02-10T06:35:00Z"
        assert entry["tags"] == ["personal", "identity"]
        assert entry["confidence"] is None

    def test_preserves_existing_confidence(self):
        v1_0 = _make_v1_0_document()
        v1_1 = migrate_v1_0_to_v1_1(v1_0)

        entry = v1_1["memories"]["relationships"]["collaboration_style"]
        assert entry["confidence"] == 0.85

    def test_preserves_different_timestamps(self):
        """Verify entries with different timestamps keep their original values."""
        v1_0 = _make_v1_0_document()
        v1_1 = migrate_v1_0_to_v1_1(v1_0)

        user_entry = v1_1["memories"]["user"]["first_name"]
        assistant_entry = v1_1["memories"]["assistant"]["name"]
        assert user_entry["created_at"] == "2026-02-10T06:35:00Z"
        assert assistant_entry["created_at"] == "2026-02-09T00:00:00Z"

    def test_all_entries_get_new_fields(self):
        v1_0 = _make_v1_0_document()
        v1_1 = migrate_v1_0_to_v1_1(v1_0)

        new_fields = {"importance", "source", "access_count", "last_accessed", "status"}
        for _cat_name, entries in v1_1["memories"].items():
            for key, entry in entries.items():
                for field_name in new_fields:
                    assert field_name in entry, f"Missing '{field_name}' in {_cat_name}.{key}"

    def test_does_not_mutate_input(self):
        v1_0 = _make_v1_0_document()
        original_copy = copy.deepcopy(v1_0)
        migrate_v1_0_to_v1_1(v1_0)
        assert v1_0 == original_copy

    def test_preserves_session_count_if_already_present(self):
        """If session_count already exists (edge case), preserve it."""
        v1_0 = _make_v1_0_document()
        v1_0["session_count"] = 42
        v1_1 = migrate_v1_0_to_v1_1(v1_0)
        assert v1_1["session_count"] == 42

    def test_migrated_entries_parse_as_memory_entry(self):
        """Verify migrated entries are valid MemoryEntry input."""
        v1_0 = _make_v1_0_document()
        v1_1 = migrate_v1_0_to_v1_1(v1_0)

        for _cat_name, entries in v1_1["memories"].items():
            for _key, entry_data in entries.items():
                # Add links field since MemoryEntry now expects it for full round-trip
                entry_data.setdefault("links", [])
                entry = MemoryEntry.from_dict(entry_data)
                assert entry.value == entry_data["value"]
                assert entry.to_dict() == entry_data


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
        import pytest

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
        """Entries from v1.1 data (no links field) get empty links."""
        data = {
            "value": "old entry",
            "created_at": "2026-02-10T06:35:00Z",
            "updated_at": "2026-02-10T06:35:00Z",
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.links == []


# -- Migration v1.1 -> v1.2 ---------------------------------------------------


def _make_v1_1_document() -> dict:
    """Create a v1.1 document for migration testing."""
    return {
        "schema_version": "1.1",
        "session_count": 5,
        "memories": {
            "user": {
                "name": {
                    "value": "Alice",
                    "created_at": "2026-02-10T06:35:00Z",
                    "updated_at": "2026-02-10T06:35:00Z",
                    "tags": ["identity"],
                    "confidence": None,
                    "importance": 8,
                    "source": {"type": "user-stated", "detail": None},
                    "access_count": 3,
                    "last_accessed": "2026-02-10T10:00:00Z",
                    "status": "active",
                },
            },
            "learnings": {
                "git_tip": {
                    "value": "Use atomic commits",
                    "created_at": "2026-02-10T07:00:00Z",
                    "updated_at": "2026-02-10T07:00:00Z",
                    "tags": ["git", "workflow"],
                    "confidence": 0.9,
                    "importance": 6,
                    "source": {"type": "session", "detail": None},
                    "access_count": 0,
                    "last_accessed": None,
                    "status": "active",
                },
            },
        },
    }


class TestMigrationV11ToV12:
    def test_bumps_schema_version(self):
        v1_1 = _make_v1_1_document()
        v1_2 = migrate_v1_1_to_v1_2(v1_1)
        assert v1_2["schema_version"] == "1.2"

    def test_adds_links_to_every_entry(self):
        v1_1 = _make_v1_1_document()
        v1_2 = migrate_v1_1_to_v1_2(v1_1)

        for _cat_name, entries in v1_2["memories"].items():
            for _key, entry in entries.items():
                assert "links" in entry
                assert entry["links"] == []

    def test_preserves_original_data(self):
        v1_1 = _make_v1_1_document()
        v1_2 = migrate_v1_1_to_v1_2(v1_1)

        entry = v1_2["memories"]["user"]["name"]
        assert entry["value"] == "Alice"
        assert entry["importance"] == 8
        assert entry["access_count"] == 3

    def test_preserves_session_count(self):
        v1_1 = _make_v1_1_document()
        v1_2 = migrate_v1_1_to_v1_2(v1_1)
        assert v1_2["session_count"] == 5

    def test_does_not_mutate_input(self):
        v1_1 = _make_v1_1_document()
        original_copy = copy.deepcopy(v1_1)
        migrate_v1_1_to_v1_2(v1_1)
        assert v1_1 == original_copy


# -- Chained migration v1.0 -> v1.2 ------------------------------------------


class TestChainedMigration:
    def test_v1_0_to_v1_2_via_chain(self):
        """Apply v1.0 -> v1.1 -> v1.2 sequentially."""
        v1_0 = _make_v1_0_document()
        v1_1 = migrate_v1_0_to_v1_1(v1_0)
        v1_2 = migrate_v1_1_to_v1_2(v1_1)

        assert v1_2["schema_version"] == "1.2"
        assert v1_2["session_count"] == 0

        # All entries have both v1.1 and v1.2 fields
        entry = v1_2["memories"]["user"]["first_name"]
        assert entry["importance"] == DEFAULT_IMPORTANCE
        assert entry["source"] == {"type": "session", "detail": None}
        assert entry["access_count"] == 0
        assert entry["status"] == "active"
        assert entry["links"] == []

        # Original data preserved
        assert entry["value"] == "Francisco"
        assert entry["tags"] == ["personal", "identity"]

    def test_chained_migration_preserves_all_entries(self):
        v1_0 = _make_v1_0_document()
        v1_1 = migrate_v1_0_to_v1_1(v1_0)
        v1_2 = migrate_v1_1_to_v1_2(v1_1)

        # Count entries: same number as original
        original_count = sum(len(e) for e in v1_0["memories"].values())
        migrated_count = sum(len(e) for e in v1_2["memories"].values())
        assert migrated_count == original_count
