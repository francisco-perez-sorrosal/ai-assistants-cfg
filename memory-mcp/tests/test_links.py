"""Tests for link CRUD, connections, auto-linking, and link cleanup."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from memory_mcp.schema import SCHEMA_VERSION
from memory_mcp.store import (
    MAX_AUTO_LINKS_PER_REMEMBER,
    MemoryStore,
)

# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def memory_file(tmp_path: Path) -> Path:
    return tmp_path / "memory.json"


@pytest.fixture
def store(memory_file: Path) -> MemoryStore:
    return MemoryStore(memory_file)


def _make_entry(
    value: str,
    *,
    tags: list[str] | None = None,
    importance: int = 5,
    links: list[dict] | None = None,
) -> dict:
    """Build a raw v1.2 entry dict for direct file injection."""
    return {
        "value": value,
        "created_at": "2026-02-10T06:35:00Z",
        "updated_at": "2026-02-10T06:35:00Z",
        "tags": tags or [],
        "confidence": None,
        "importance": importance,
        "source": {"type": "session", "detail": None},
        "access_count": 0,
        "last_accessed": None,
        "status": "active",
        "links": links or [],
    }


def _write_store(memory_file: Path, entries_by_category: dict) -> None:
    """Write a pre-built memory store to the file."""
    memories = {
        cat: {} for cat in
        ("user", "assistant", "project", "relationships", "tools", "learnings")
    }
    for cat, entries in entries_by_category.items():
        memories[cat] = entries
    doc = {
        "schema_version": SCHEMA_VERSION,
        "session_count": 1,
        "memories": memories,
    }
    memory_file.write_text(json.dumps(doc, indent=2) + "\n")


# -- add_link: creates link ---------------------------------------------------


class TestAddLink:
    def test_creates_link(self, store: MemoryStore):
        store.remember("user", "name", "Alice", tags=["identity"])
        store.remember("user", "email", "alice@example.com", tags=["contact"])

        result = store.add_link("user", "name", "user", "email", "related-to")
        assert result["link_created"] is True
        assert result["source"] == "user.name"
        assert result["target"] == "user.email"
        assert result["relation"] == "related-to"

    def test_link_persisted_to_file(self, store: MemoryStore, memory_file: Path):
        store.remember("user", "name", "Alice")
        store.remember("learnings", "tip", "Use pytest")

        store.add_link("user", "name", "learnings", "tip", "depends-on")

        data = json.loads(memory_file.read_text())
        links = data["memories"]["user"]["name"]["links"]
        assert len(links) == 1
        assert links[0]["target"] == "learnings.tip"
        assert links[0]["relation"] == "depends-on"

    def test_cross_category_link(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        store.remember("tools", "editor", "vim")

        result = store.add_link("user", "name", "tools", "editor", "elaborates")
        assert result["link_created"] is True
        assert result["target"] == "tools.editor"


# -- add_link: rejects invalid relation ---------------------------------------


class TestAddLinkInvalidRelation:
    def test_rejects_invalid_relation(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        store.remember("user", "email", "alice@example.com")

        with pytest.raises(ValueError, match="Invalid relation"):
            store.add_link("user", "name", "user", "email", "unknown-relation")


# -- add_link: rejects non-existent entries -----------------------------------


class TestAddLinkNonExistent:
    def test_rejects_nonexistent_source(self, store: MemoryStore):
        store.remember("user", "email", "alice@example.com")

        with pytest.raises(KeyError, match="Source entry"):
            store.add_link("user", "ghost", "user", "email", "related-to")

    def test_rejects_nonexistent_target(self, store: MemoryStore):
        store.remember("user", "name", "Alice")

        with pytest.raises(KeyError, match="Target entry"):
            store.add_link("user", "name", "user", "ghost", "related-to")


# -- add_link: prevents duplicate links ---------------------------------------


class TestAddLinkDuplicate:
    def test_prevents_duplicate_same_target_and_relation(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        store.remember("user", "email", "alice@example.com")

        store.add_link("user", "name", "user", "email", "related-to")
        result = store.add_link("user", "name", "user", "email", "related-to")
        assert result["link_created"] is False
        assert result["reason"] == "duplicate"

    def test_allows_different_relation_to_same_target(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        store.remember("user", "email", "alice@example.com")

        store.add_link("user", "name", "user", "email", "related-to")
        result = store.add_link("user", "name", "user", "email", "elaborates")
        assert result["link_created"] is True

    def test_duplicate_check_does_not_add_extra(self, store: MemoryStore, memory_file: Path):
        store.remember("user", "name", "Alice")
        store.remember("user", "email", "alice@example.com")

        store.add_link("user", "name", "user", "email", "related-to")
        store.add_link("user", "name", "user", "email", "related-to")

        data = json.loads(memory_file.read_text())
        links = data["memories"]["user"]["name"]["links"]
        assert len(links) == 1


# -- remove_link: removes existing link --------------------------------------


class TestRemoveLink:
    def test_removes_existing_link(self, store: MemoryStore, memory_file: Path):
        store.remember("user", "name", "Alice")
        store.remember("user", "email", "alice@example.com")

        store.add_link("user", "name", "user", "email", "related-to")
        result = store.remove_link("user", "name", "user", "email")
        assert result["link_removed"] is True

        data = json.loads(memory_file.read_text())
        links = data["memories"]["user"]["name"]["links"]
        assert len(links) == 0

    def test_removes_all_relations_to_target(self, store: MemoryStore, memory_file: Path):
        """remove_link removes all links to the target, regardless of relation."""
        store.remember("user", "name", "Alice")
        store.remember("user", "email", "alice@example.com")

        store.add_link("user", "name", "user", "email", "related-to")
        store.add_link("user", "name", "user", "email", "elaborates")

        result = store.remove_link("user", "name", "user", "email")
        assert result["link_removed"] is True

        data = json.loads(memory_file.read_text())
        links = data["memories"]["user"]["name"]["links"]
        assert len(links) == 0


# -- remove_link: error on non-existent link ----------------------------------


class TestRemoveLinkErrors:
    def test_error_on_nonexistent_link(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        store.remember("user", "email", "alice@example.com")

        with pytest.raises(KeyError, match="No link from"):
            store.remove_link("user", "name", "user", "email")

    def test_error_on_nonexistent_source(self, store: MemoryStore):
        with pytest.raises(KeyError, match="Source entry"):
            store.remove_link("user", "ghost", "user", "email")


# -- connections: shows outgoing links ----------------------------------------


class TestConnectionsOutgoing:
    def test_shows_outgoing_links(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        store.remember("user", "email", "alice@example.com")
        store.remember("tools", "editor", "vim")

        store.add_link("user", "name", "user", "email", "related-to")
        store.add_link("user", "name", "tools", "editor", "depends-on")

        result = store.connections("user", "name")
        assert len(result["outgoing"]) == 2

        targets = {o["target"] for o in result["outgoing"]}
        assert "user.email" in targets
        assert "tools.editor" in targets

    def test_outgoing_includes_entry_summary(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        store.remember("user", "email", "alice@example.com")

        store.add_link("user", "name", "user", "email", "related-to")

        result = store.connections("user", "name")
        outgoing = result["outgoing"][0]
        assert outgoing["entry_summary"] == "alice@example.com"
        assert outgoing["relation"] == "related-to"

    def test_no_outgoing_links(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        result = store.connections("user", "name")
        assert result["outgoing"] == []


# -- connections: shows incoming links (reverse lookup) -----------------------


class TestConnectionsIncoming:
    def test_shows_incoming_links(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        store.remember("user", "email", "alice@example.com")

        store.add_link("user", "email", "user", "name", "elaborates")

        result = store.connections("user", "name")
        assert len(result["incoming"]) == 1
        incoming = result["incoming"][0]
        assert incoming["source"] == "user.email"
        assert incoming["relation"] == "elaborates"
        assert incoming["entry_summary"] == "alice@example.com"

    def test_multiple_incoming_links(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        store.remember("user", "email", "alice@example.com")
        store.remember("tools", "editor", "vim")

        store.add_link("user", "email", "user", "name", "elaborates")
        store.add_link("tools", "editor", "user", "name", "depends-on")

        result = store.connections("user", "name")
        assert len(result["incoming"]) == 2
        sources = {i["source"] for i in result["incoming"]}
        assert "user.email" in sources
        assert "tools.editor" in sources

    def test_no_incoming_links(self, store: MemoryStore):
        store.remember("user", "name", "Alice")
        result = store.connections("user", "name")
        assert result["incoming"] == []

    def test_connections_on_nonexistent_entry(self, store: MemoryStore):
        with pytest.raises(KeyError, match="not found"):
            store.connections("user", "ghost")


# -- Auto-linking in remember -------------------------------------------------


class TestAutoLinking:
    def test_auto_link_on_tag_overlap(self, store: MemoryStore, memory_file: Path):
        """New entry with 2+ tag overlap gets auto-linked to existing."""
        store.remember(
            "user", "name", "Alice",
            tags=["identity", "personal", "profile"],
            force=True,
        )
        store.remember(
            "user", "email", "alice@example.com",
            tags=["identity", "personal", "contact"],
            force=True,
        )

        # Verify auto-link was created from email -> name
        data = json.loads(memory_file.read_text())
        email_links = data["memories"]["user"]["email"]["links"]
        assert len(email_links) >= 1
        assert any(
            lk["target"] == "user.name" and lk["relation"] == "related-to"
            for lk in email_links
        )

    def test_no_auto_link_below_threshold(self, store: MemoryStore, memory_file: Path):
        """Entries with fewer than AUTO_LINK_TAG_OVERLAP_THRESHOLD shared tags get no auto-link."""
        store.remember("user", "name", "Alice", tags=["identity"], force=True)
        store.remember("user", "email", "alice@example.com", tags=["contact"], force=True)

        data = json.loads(memory_file.read_text())
        email_links = data["memories"]["user"]["email"]["links"]
        assert len(email_links) == 0

    def test_no_auto_link_on_update(self, store: MemoryStore, memory_file: Path):
        """Updates (existing key) should NOT trigger auto-linking."""
        store.remember(
            "user", "name", "Alice",
            tags=["identity", "personal", "profile"],
            force=True,
        )
        store.remember(
            "user", "email", "alice@example.com",
            tags=["identity", "personal", "contact"],
            force=True,
        )

        # Clear the auto-link from email for the update test
        data = json.loads(memory_file.read_text())
        data["memories"]["user"]["email"]["links"] = []
        memory_file.write_text(json.dumps(data, indent=2) + "\n")

        # Reload store and update the existing key
        store2 = MemoryStore(memory_file)
        result = store2.remember(
            "user", "email", "newalice@example.com",
            tags=["identity", "personal", "contact"],
        )
        assert result["action"] == "UPDATE"

        data = json.loads(memory_file.read_text())
        email_links = data["memories"]["user"]["email"]["links"]
        assert len(email_links) == 0

    def test_auto_link_limit(self, store: MemoryStore, memory_file: Path):
        """Auto-linking creates at most MAX_AUTO_LINKS_PER_REMEMBER links."""
        shared_tags = ["python", "coding", "development"]
        # Create more entries than the limit
        for i in range(MAX_AUTO_LINKS_PER_REMEMBER + 2):
            store.remember(
                "learnings", f"entry_{i}", f"Lesson {i}",
                tags=shared_tags + [f"unique_{i}"],
                force=True,
            )

        # The last entry should have at most MAX_AUTO_LINKS_PER_REMEMBER links
        data = json.loads(memory_file.read_text())
        last_key = f"entry_{MAX_AUTO_LINKS_PER_REMEMBER + 1}"
        last_links = data["memories"]["learnings"][last_key]["links"]
        assert len(last_links) <= MAX_AUTO_LINKS_PER_REMEMBER

    def test_auto_link_no_tags(self, store: MemoryStore, memory_file: Path):
        """Entries without tags don't get auto-linked."""
        store.remember("user", "name", "Alice", force=True)
        store.remember("user", "email", "alice@example.com", force=True)

        data = json.loads(memory_file.read_text())
        email_links = data["memories"]["user"]["email"]["links"]
        assert len(email_links) == 0


# -- Forget with link cleanup -------------------------------------------------


class TestForgetLinkCleanup:
    def test_incoming_links_removed_on_forget(self, store: MemoryStore, memory_file: Path):
        """When an entry is deleted, all incoming links from other entries are removed."""
        store.remember("user", "name", "Alice")
        store.remember("user", "email", "alice@example.com")
        store.remember("tools", "editor", "vim")

        store.add_link("user", "email", "user", "name", "elaborates")
        store.add_link("tools", "editor", "user", "name", "depends-on")

        # Verify links exist before forget
        data = json.loads(memory_file.read_text())
        assert len(data["memories"]["user"]["email"]["links"]) == 1
        assert len(data["memories"]["tools"]["editor"]["links"]) == 1

        # Delete the target entry
        store.forget("user", "name")

        # Verify incoming links are cleaned up
        data = json.loads(memory_file.read_text())
        assert len(data["memories"]["user"]["email"]["links"]) == 0
        assert len(data["memories"]["tools"]["editor"]["links"]) == 0

    def test_other_links_preserved_on_forget(self, store: MemoryStore, memory_file: Path):
        """Links not pointing to the deleted entry are preserved."""
        store.remember("user", "name", "Alice")
        store.remember("user", "email", "alice@example.com")
        store.remember("tools", "editor", "vim")

        store.add_link("user", "email", "user", "name", "elaborates")
        store.add_link("user", "email", "tools", "editor", "related-to")

        store.forget("user", "name")

        # The link to tools.editor should be preserved
        data = json.loads(memory_file.read_text())
        email_links = data["memories"]["user"]["email"]["links"]
        assert len(email_links) == 1
        assert email_links[0]["target"] == "tools.editor"


# -- Migration in store (chained) ---------------------------------------------


class TestStoreMigrationChain:
    def test_v1_0_file_migrated_to_v1_2(self, memory_file: Path):
        """A v1.0 file should be auto-migrated through v1.1 to v1.2."""
        v1_0 = {
            "schema_version": "1.0",
            "memories": {
                "user": {
                    "name": {
                        "value": "Alice",
                        "created_at": "2026-02-10T06:35:00Z",
                        "updated_at": "2026-02-10T06:35:00Z",
                        "tags": ["identity"],
                        "confidence": None,
                    },
                },
            },
        }
        memory_file.write_text(json.dumps(v1_0, indent=2) + "\n")

        MemoryStore(memory_file)

        data = json.loads(memory_file.read_text())
        assert data["schema_version"] == "1.2"

        entry = data["memories"]["user"]["name"]
        # v1.1 fields
        assert entry["importance"] == 5
        assert entry["source"] == {"type": "session", "detail": None}
        assert entry["access_count"] == 0
        assert entry["status"] == "active"
        # v1.2 field
        assert entry["links"] == []

    def test_v1_1_file_migrated_to_v1_2(self, memory_file: Path):
        """A v1.1 file should be auto-migrated to v1.2."""
        v1_1 = {
            "schema_version": "1.1",
            "session_count": 3,
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
                        "access_count": 5,
                        "last_accessed": "2026-02-10T10:00:00Z",
                        "status": "active",
                    },
                },
            },
        }
        memory_file.write_text(json.dumps(v1_1, indent=2) + "\n")

        MemoryStore(memory_file)

        data = json.loads(memory_file.read_text())
        assert data["schema_version"] == "1.2"
        assert data["session_count"] == 3

        entry = data["memories"]["user"]["name"]
        assert entry["links"] == []
        # Preserved v1.1 fields
        assert entry["importance"] == 8
        assert entry["access_count"] == 5

    def test_v1_2_file_not_migrated(self, memory_file: Path):
        """A v1.2 file should not trigger migration."""
        v1_2 = {
            "schema_version": "1.2",
            "session_count": 10,
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
                        "access_count": 5,
                        "last_accessed": "2026-02-10T10:00:00Z",
                        "status": "active",
                        "links": [{"target": "tools.editor", "relation": "related-to"}],
                    },
                },
            },
        }
        memory_file.write_text(json.dumps(v1_2, indent=2) + "\n")

        MemoryStore(memory_file)

        data = json.loads(memory_file.read_text())
        assert data["schema_version"] == "1.2"
        # Links preserved, not reset
        assert len(data["memories"]["user"]["name"]["links"]) == 1

    def test_v1_0_migration_creates_backups(self, memory_file: Path):
        """v1.0 migration should create both v1.0 and v1.1 backups."""
        v1_0 = {
            "schema_version": "1.0",
            "memories": {
                "user": {
                    "name": {
                        "value": "Alice",
                        "created_at": "2026-02-10T06:35:00Z",
                        "updated_at": "2026-02-10T06:35:00Z",
                        "tags": [],
                        "confidence": None,
                    },
                },
            },
        }
        memory_file.write_text(json.dumps(v1_0, indent=2) + "\n")

        MemoryStore(memory_file)

        # v1.0 backup
        v1_0_backup = memory_file.with_name(memory_file.stem + ".pre-migration-1.0.json")
        assert v1_0_backup.exists()
        backup_data = json.loads(v1_0_backup.read_text())
        assert backup_data["schema_version"] == "1.0"

        # v1.1 backup
        v1_1_backup = memory_file.with_name(memory_file.stem + ".pre-migration-1.1.json")
        assert v1_1_backup.exists()
        backup_data = json.loads(v1_1_backup.read_text())
        assert backup_data["schema_version"] == "1.1"
