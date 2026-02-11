"""Tests for MemoryStore CRUD operations and file I/O."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from memory_mcp.schema import SCHEMA_VERSION, VALID_CATEGORIES
from memory_mcp.store import PRE_MIGRATION_SUFFIX, MemoryStore

# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def memory_file(tmp_path: Path) -> Path:
    """Return a path for a new memory file (not yet created)."""
    return tmp_path / "memory.json"


@pytest.fixture
def store(memory_file: Path) -> MemoryStore:
    """Return a MemoryStore backed by a fresh empty file."""
    return MemoryStore(memory_file)


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
            "tools": {
                "clipboard": {
                    "value": "pbcopy / pbpaste",
                    "created_at": "2026-02-10T06:35:00Z",
                    "updated_at": "2026-02-10T06:35:00Z",
                    "tags": ["user-preference", "cli"],
                    "confidence": None,
                },
            },
        },
    }


# -- Init and file creation ---------------------------------------------------


class TestStoreInit:
    def test_creates_file_if_missing(self, memory_file: Path):
        assert not memory_file.exists()
        MemoryStore(memory_file)
        assert memory_file.exists()

    def test_creates_parent_directories(self, tmp_path: Path):
        deep_path = tmp_path / "a" / "b" / "c" / "memory.json"
        MemoryStore(deep_path)
        assert deep_path.exists()

    def test_new_file_has_valid_structure(self, memory_file: Path):
        MemoryStore(memory_file)
        data = json.loads(memory_file.read_text())
        assert data["schema_version"] == SCHEMA_VERSION
        assert data["session_count"] == 0
        assert set(data["memories"].keys()) == set(VALID_CATEGORIES)

    def test_loads_existing_v1_2_file(self, memory_file: Path):
        existing = {
            "schema_version": "1.2",
            "session_count": 5,
            "memories": {"user": {"name": {"value": "Test", "created_at": "2026-01-01T00:00:00Z",
                                           "updated_at": "2026-01-01T00:00:00Z", "tags": [],
                                           "confidence": None, "importance": 5,
                                           "source": {"type": "session", "detail": None},
                                           "access_count": 0, "last_accessed": None,
                                           "status": "active", "links": []}}},
        }
        memory_file.write_text(json.dumps(existing, indent=2) + "\n")
        store = MemoryStore(memory_file)
        result = store.status()
        assert result["session_count"] == 5


# -- Auto-migration -----------------------------------------------------------


class TestAutoMigration:
    def test_migrates_v1_0_to_v1_2(self, memory_file: Path):
        v1_0 = _make_v1_0_document()
        memory_file.write_text(json.dumps(v1_0, indent=2) + "\n")
        MemoryStore(memory_file)

        data = json.loads(memory_file.read_text())
        assert data["schema_version"] == "1.2"
        assert "session_count" in data

        entry = data["memories"]["user"]["first_name"]
        assert "importance" in entry
        assert "source" in entry
        assert "access_count" in entry
        assert "status" in entry
        assert "links" in entry
        assert entry["links"] == []

    def test_creates_pre_migration_backup(self, memory_file: Path):
        v1_0 = _make_v1_0_document()
        memory_file.write_text(json.dumps(v1_0, indent=2) + "\n")
        MemoryStore(memory_file)

        backup_path = memory_file.with_name(memory_file.stem + PRE_MIGRATION_SUFFIX)
        assert backup_path.exists()
        backup_data = json.loads(backup_path.read_text())
        assert backup_data["schema_version"] == "1.0"

    def test_preserves_original_data_after_migration(self, memory_file: Path):
        v1_0 = _make_v1_0_document()
        memory_file.write_text(json.dumps(v1_0, indent=2) + "\n")
        MemoryStore(memory_file)

        data = json.loads(memory_file.read_text())
        entry = data["memories"]["user"]["first_name"]
        assert entry["value"] == "Francisco"
        assert entry["created_at"] == "2026-02-10T06:35:00Z"
        assert entry["tags"] == ["personal", "identity"]

    def test_skips_migration_for_v1_2(self, memory_file: Path):
        v1_2 = {
            "schema_version": "1.2",
            "session_count": 3,
            "memories": {"user": {}},
        }
        memory_file.write_text(json.dumps(v1_2, indent=2) + "\n")
        MemoryStore(memory_file)

        backup_path = memory_file.with_name(memory_file.stem + PRE_MIGRATION_SUFFIX)
        assert not backup_path.exists()


# -- CRUD cycle: remember -> recall -> forget ---------------------------------


class TestCRUDCycle:
    def test_remember_creates_new_entry(self, store: MemoryStore):
        result = store.remember("user", "name", "Alice", tags=["identity"])
        assert result["action"] == "ADD"
        assert result["entry"]["value"] == "Alice"
        assert "identity" in result["entry"]["tags"]

    def test_remember_updates_existing_entry(self, store: MemoryStore):
        store.remember("user", "name", "Alice", tags=["identity"])
        result = store.remember("user", "name", "Bob", tags=["updated"])
        assert result["action"] == "UPDATE"
        assert result["entry"]["value"] == "Bob"
        assert "identity" in result["entry"]["tags"]
        assert "updated" in result["entry"]["tags"]

    def test_remember_preserves_created_at_on_update(self, store: MemoryStore):
        add_result = store.remember("user", "name", "Alice")
        created_at = add_result["entry"]["created_at"]
        update_result = store.remember("user", "name", "Bob")
        assert update_result["entry"]["created_at"] == created_at
        assert update_result["entry"]["updated_at"] != created_at

    def test_recall_single_entry(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        result = store.recall("user", "name")
        assert "name" in result["entries"]
        assert result["entries"]["name"]["value"] == "Alice"

    def test_recall_all_entries_in_category(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        store.remember("user", "email", "alice@example.com")
        result = store.recall("user")
        assert len(result["entries"]) == 2
        assert "name" in result["entries"]
        assert "email" in result["entries"]

    def test_forget_removes_entry(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        result = store.forget("user", "name")
        assert result["removed"]["value"] == "Alice"
        assert "backup_path" in result

        with pytest.raises(KeyError):
            store.recall("user", "name")

    def test_forget_creates_backup_file(self, store: MemoryStore, memory_file: Path):
        store.remember("user", "name", "Alice")
        result = store.forget("user", "name")
        backup_path = Path(result["backup_path"])
        assert backup_path.exists()
        backup_data = json.loads(backup_path.read_text())
        assert "memories" in backup_data

    def test_forget_nonexistent_key_raises(self, store: MemoryStore):
        with pytest.raises(KeyError):
            store.forget("user", "nonexistent")

    def test_recall_nonexistent_key_raises(self, store: MemoryStore):
        with pytest.raises(KeyError):
            store.recall("user", "nonexistent")


# -- Access tracking ----------------------------------------------------------


class TestAccessTracking:
    def test_recall_increments_access_count(self, store: MemoryStore):
        store.remember("user", "name", "Alice")

        result1 = store.recall("user", "name")
        assert result1["entries"]["name"]["access_count"] == 1

        result2 = store.recall("user", "name")
        assert result2["entries"]["name"]["access_count"] == 2

    def test_recall_sets_last_accessed(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        result = store.recall("user", "name")
        assert result["entries"]["name"]["last_accessed"] is not None

    def test_recall_all_increments_each_entry(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        store.remember("user", "email", "alice@example.com")

        store.recall("user")

        result = store.recall("user")
        for entry in result["entries"].values():
            assert entry["access_count"] == 2

    def test_search_increments_access_count(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        store.search("Alice")

        result = store.recall("user", "name")
        # recall adds +1, search already added +1 = 2
        assert result["entries"]["name"]["access_count"] == 2

    def test_access_count_persisted_to_file(self, store: MemoryStore, memory_file: Path):
        store.remember("user", "name", "Alice")
        store.recall("user", "name")

        data = json.loads(memory_file.read_text())
        assert data["memories"]["user"]["name"]["access_count"] == 1


# -- Search -------------------------------------------------------------------


class TestSearch:
    def test_search_by_value(self, store: MemoryStore):
        store.remember("user", "name", "Alice Wonderland")
        result = store.search("alice")
        assert len(result["results"]) == 1
        assert "value" in result["results"][0]["match_reason"]

    def test_search_by_key(self, store: MemoryStore):
        store.remember("user", "email", "test@example.com")
        result = store.search("email")
        assert len(result["results"]) == 1
        assert "key" in result["results"][0]["match_reason"]

    def test_search_by_tag(self, store: MemoryStore):
        store.remember("user", "name", "Alice", tags=["identity"])
        result = store.search("identity")
        assert len(result["results"]) == 1
        assert "tag" in result["results"][0]["match_reason"]

    def test_search_within_category(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        store.remember("tools", "editor", "Alice-editor")
        result = store.search("alice", category="user")
        assert len(result["results"]) == 1
        assert result["results"][0]["category"] == "user"

    def test_search_no_results(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        result = store.search("nonexistent")
        assert len(result["results"]) == 0

    def test_search_case_insensitive(self, store: MemoryStore):
        store.remember("user", "name", "ALICE")
        result = store.search("alice")
        assert len(result["results"]) == 1


# -- Session start ------------------------------------------------------------


class TestSessionStart:
    def test_increments_session_count(self, store: MemoryStore):
        result1 = store.session_start()
        assert result1["session_count"] == 1
        result2 = store.session_start()
        assert result2["session_count"] == 2

    def test_returns_category_summary(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        result = store.session_start()
        assert result["categories"]["user"] == 1
        assert result["total"] == 1

    def test_session_count_persisted(self, store: MemoryStore, memory_file: Path):
        store.session_start()
        store.session_start()
        data = json.loads(memory_file.read_text())
        assert data["session_count"] == 2


# -- Atomic write -------------------------------------------------------------


class TestAtomicWrite:
    def test_file_exists_after_save(self, store: MemoryStore, memory_file: Path):
        store.remember("user", "name", "Alice")
        assert memory_file.exists()

    def test_file_contains_valid_json(self, store: MemoryStore, memory_file: Path):
        store.remember("user", "name", "Alice")
        data = json.loads(memory_file.read_text())
        assert data["memories"]["user"]["name"]["value"] == "Alice"

    def test_file_has_trailing_newline(self, store: MemoryStore, memory_file: Path):
        store.remember("user", "name", "Alice")
        content = memory_file.read_text()
        assert content.endswith("\n")

    def test_file_uses_two_space_indent(self, store: MemoryStore, memory_file: Path):
        store.remember("user", "name", "Alice")
        content = memory_file.read_text()
        # Check that the JSON uses 2-space indentation (not 4)
        assert '  "schema_version"' in content


# -- Validation ---------------------------------------------------------------


class TestValidation:
    def test_invalid_category_raises(self, store: MemoryStore):
        with pytest.raises(ValueError, match="Invalid category"):
            store.remember("invalid_cat", "key", "value")

    def test_importance_clamped_to_range(self, store: MemoryStore):
        result_low = store.remember("user", "low", "test", importance=0)
        assert result_low["entry"]["importance"] == 1

        result_high = store.remember("user", "high", "test", importance=99)
        assert result_high["entry"]["importance"] == 10


# -- Status -------------------------------------------------------------------


class TestStatus:
    def test_status_returns_counts(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        store.remember("tools", "editor", "vim")
        result = store.status()
        assert result["categories"]["user"] == 1
        assert result["categories"]["tools"] == 1
        assert result["total"] == 2
        assert result["schema_version"] == SCHEMA_VERSION

    def test_status_returns_file_size(self, store: MemoryStore):
        result = store.status()
        assert "file_size" in result
        assert "B" in result["file_size"] or "KB" in result["file_size"]


# -- Export -------------------------------------------------------------------


class TestExport:
    def test_export_markdown(self, store: MemoryStore):
        store.remember("user", "name", "Alice", tags=["identity"])
        result = store.export("markdown")
        assert "# Memory Export" in result["content"]
        assert "Alice" in result["content"]
        assert "identity" in result["content"]

    def test_export_json(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        result = store.export("json")
        data = json.loads(result["content"])
        assert data["memories"]["user"]["name"]["value"] == "Alice"


# -- About me / about us -----------------------------------------------------


class TestAboutMe:
    def test_aggregates_user_entries(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        store.remember("user", "email", "alice@example.com")
        result = store.about_me()
        assert "Alice" in result["profile"]
        assert "alice@example.com" in result["profile"]

    def test_includes_user_facing_relationships(self, store: MemoryStore):
        store.remember("relationships", "style", "direct", tags=["user-facing"])
        result = store.about_me()
        assert "direct" in result["profile"]
        assert "Relationship Context" in result["profile"]

    def test_includes_user_preference_tools(self, store: MemoryStore):
        store.remember("tools", "editor", "vim", tags=["user-preference"])
        result = store.about_me()
        assert "vim" in result["profile"]
        assert "Tool Preferences" in result["profile"]

    def test_excludes_non_user_facing_relationships(self, store: MemoryStore):
        store.remember("relationships", "internal", "hidden", tags=["internal-only"])
        result = store.about_me()
        assert "hidden" not in result["profile"] or "Relationship Context" not in result["profile"]

    def test_empty_profile(self, store: MemoryStore):
        result = store.about_me()
        assert result["profile"] == "No user profile data found."


class TestAboutUs:
    def test_aggregates_relationships(self, store: MemoryStore):
        store.remember("relationships", "style", "collaborative")
        result = store.about_us()
        assert "collaborative" in result["profile"]
        assert "Our Relationship" in result["profile"]

    def test_includes_assistant_identity(self, store: MemoryStore):
        store.remember("assistant", "name", "Kael")
        result = store.about_us()
        assert "Kael" in result["profile"]
        assert "Assistant Identity" in result["profile"]

    def test_empty_profile(self, store: MemoryStore):
        result = store.about_us()
        assert result["profile"] == "No relationship data found."
