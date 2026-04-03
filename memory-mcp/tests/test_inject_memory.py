"""Tests for inject_memory.py hook: importance tiers, agent-type routing, locking."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest

# -- Load the hook module from its file path (not a package) ------------------

_HOOK_PATH = Path(__file__).resolve().parents[2] / ".claude-plugin" / "hooks" / "inject_memory.py"


def _load_hook_module():
    """Import inject_memory.py as a module from its file path."""
    spec = importlib.util.spec_from_file_location("inject_memory", _HOOK_PATH)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


inject_memory = _load_hook_module()

# -- Fixtures -----------------------------------------------------------------


def _make_memory_json(entries: list[dict], *, path: Path) -> None:
    """Write a memory.json file from a list of entry dicts.

    Each entry dict should have: category, key, value, importance, tags.
    Optional: summary, status, invalid_at.
    """
    memories: dict[str, dict] = {}
    for e in entries:
        cat = e["category"]
        if cat not in memories:
            memories[cat] = {}
        memories[cat][e["key"]] = {
            "value": e.get("value", ""),
            "summary": e.get("summary", ""),
            "importance": e.get("importance", 5),
            "tags": e.get("tags", []),
            "status": e.get("status", "active"),
            "invalid_at": e.get("invalid_at"),
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
    ai_state = path / ".ai-state"
    ai_state.mkdir(parents=True, exist_ok=True)
    (ai_state / "memory.json").write_text(
        json.dumps({"schema_version": "2.0", "memories": memories}),
        encoding="utf-8",
    )


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Return a temporary project directory."""
    return tmp_path


# -- Importance tier tests ----------------------------------------------------


class TestImportanceTiers:
    def test_tier1_always_injected(self, project_dir: Path):
        """Entries with importance >= 7 are always present in output."""
        _make_memory_json(
            [
                {
                    "category": "learnings",
                    "key": "critical",
                    "value": "Critical info",
                    "importance": 9,
                    "tags": [],
                },
                {
                    "category": "learnings",
                    "key": "important",
                    "value": "Important info",
                    "importance": 7,
                    "tags": [],
                },
            ],
            path=project_dir,
        )
        entries = inject_memory._collect_active_entries(
            json.loads((project_dir / ".ai-state" / "memory.json").read_text())["memories"]
        )
        result = inject_memory._build_tiered_output(entries, "_default")
        assert "critical" in result
        assert "important" in result

    def test_tier2_included_when_budget_allows(self, project_dir: Path):
        """Entries with importance 4-6 are included when budget allows."""
        _make_memory_json(
            [
                {
                    "category": "learnings",
                    "key": "mid",
                    "value": "Mid priority",
                    "importance": 5,
                    "tags": [],
                },
            ],
            path=project_dir,
        )
        entries = inject_memory._collect_active_entries(
            json.loads((project_dir / ".ai-state" / "memory.json").read_text())["memories"]
        )
        result = inject_memory._build_tiered_output(entries, "_default")
        assert "mid" in result

    def test_tier3_never_injected(self, project_dir: Path):
        """Entries with importance 1-3 are never injected (search-only)."""
        _make_memory_json(
            [
                {
                    "category": "learnings",
                    "key": "low",
                    "value": "Low priority",
                    "importance": 3,
                    "tags": [],
                },
                {
                    "category": "learnings",
                    "key": "very_low",
                    "value": "Very low",
                    "importance": 1,
                    "tags": [],
                },
            ],
            path=project_dir,
        )
        entries = inject_memory._collect_active_entries(
            json.loads((project_dir / ".ai-state" / "memory.json").read_text())["memories"]
        )
        result = inject_memory._build_tiered_output(entries, "_default")
        assert result == ""


# -- Agent-type category ordering tests ---------------------------------------


class TestAgentTypeCategoryOrdering:
    def test_implementer_sees_learnings_first(self, project_dir: Path):
        """Implementer agent type prioritizes learnings over project."""
        _make_memory_json(
            [
                {
                    "category": "project",
                    "key": "proj_a",
                    "value": "Project info",
                    "importance": 7,
                    "tags": [],
                },
                {
                    "category": "learnings",
                    "key": "learn_a",
                    "value": "Learning info",
                    "importance": 7,
                    "tags": [],
                },
            ],
            path=project_dir,
        )
        entries = inject_memory._collect_active_entries(
            json.loads((project_dir / ".ai-state" / "memory.json").read_text())["memories"]
        )
        result = inject_memory._build_tiered_output(entries, "implementer")
        # learnings should appear before project in the output
        learn_pos = result.index("## learnings")
        proj_pos = result.index("## project")
        assert learn_pos < proj_pos

    def test_architect_sees_project_first(self, project_dir: Path):
        """Systems-architect agent type prioritizes project over learnings."""
        _make_memory_json(
            [
                {
                    "category": "project",
                    "key": "proj_a",
                    "value": "Project info",
                    "importance": 7,
                    "tags": [],
                },
                {
                    "category": "learnings",
                    "key": "learn_a",
                    "value": "Learning info",
                    "importance": 7,
                    "tags": [],
                },
            ],
            path=project_dir,
        )
        entries = inject_memory._collect_active_entries(
            json.loads((project_dir / ".ai-state" / "memory.json").read_text())["memories"]
        )
        result = inject_memory._build_tiered_output(entries, "systems-architect")
        proj_pos = result.index("## project")
        learn_pos = result.index("## learnings")
        assert proj_pos < learn_pos

    def test_unknown_agent_uses_default(self, project_dir: Path):
        """Unknown agent types fall back to _default ordering."""
        _make_memory_json(
            [
                {
                    "category": "learnings",
                    "key": "learn",
                    "value": "L",
                    "importance": 7,
                    "tags": [],
                },
                {"category": "project", "key": "proj", "value": "P", "importance": 7, "tags": []},
            ],
            path=project_dir,
        )
        entries = inject_memory._collect_active_entries(
            json.loads((project_dir / ".ai-state" / "memory.json").read_text())["memories"]
        )
        result = inject_memory._build_tiered_output(entries, "unknown-agent")
        # _default has learnings first
        learn_pos = result.index("## learnings")
        proj_pos = result.index("## project")
        assert learn_pos < proj_pos


# -- Temporal filter tests ----------------------------------------------------


class TestTemporalFilter:
    def test_entries_with_invalid_at_excluded(self, project_dir: Path):
        """Entries with invalid_at set are excluded from injection."""
        _make_memory_json(
            [
                {
                    "category": "learnings",
                    "key": "valid",
                    "value": "Still valid",
                    "importance": 7,
                    "tags": [],
                },
                {
                    "category": "learnings",
                    "key": "expired",
                    "value": "Expired",
                    "importance": 9,
                    "tags": [],
                    "invalid_at": "2026-01-01T00:00:00Z",
                },
            ],
            path=project_dir,
        )
        entries = inject_memory._collect_active_entries(
            json.loads((project_dir / ".ai-state" / "memory.json").read_text())["memories"]
        )
        keys = [e["key"] for e in entries]
        assert "valid" in keys
        assert "expired" not in keys

    def test_superseded_entries_excluded(self, project_dir: Path):
        """Entries with status=superseded are excluded from injection."""
        _make_memory_json(
            [
                {
                    "category": "learnings",
                    "key": "current",
                    "value": "Current",
                    "importance": 7,
                    "tags": [],
                },
                {
                    "category": "learnings",
                    "key": "old",
                    "value": "Old",
                    "importance": 9,
                    "tags": [],
                    "status": "superseded",
                },
            ],
            path=project_dir,
        )
        entries = inject_memory._collect_active_entries(
            json.loads((project_dir / ".ai-state" / "memory.json").read_text())["memories"]
        )
        keys = [e["key"] for e in entries]
        assert "current" in keys
        assert "old" not in keys


# -- Character budget tests ---------------------------------------------------


class TestCharacterBudget:
    def test_output_never_exceeds_max_inject_chars(self, project_dir: Path):
        """Output body stays within MAX_INJECT_CHARS budget."""
        entries_data = []
        for i in range(500):
            entries_data.append(
                {
                    "category": "learnings",
                    "key": f"entry_{i:03d}",
                    "value": f"Learning about topic {i} that is important for the project",
                    "summary": f"Topic {i} learning",
                    "importance": 7,
                    "tags": ["tag1", "tag2"],
                }
            )
        _make_memory_json(entries_data, path=project_dir)
        entries = inject_memory._collect_active_entries(
            json.loads((project_dir / ".ai-state" / "memory.json").read_text())["memories"]
        )
        result = inject_memory._build_tiered_output(entries, "_default")
        assert len(result) <= inject_memory.MAX_INJECT_CHARS + 200  # +200 for truncation footer

    def test_truncation_footer_when_entries_dropped(self, project_dir: Path):
        """Footer added when entries are truncated due to budget."""
        entries_data = []
        for i in range(500):
            entries_data.append(
                {
                    "category": "learnings",
                    "key": f"entry_{i:03d}",
                    "value": f"Learning about topic {i}",
                    "summary": f"Topic {i} learning summary text",
                    "importance": 7,
                    "tags": ["tag1", "tag2"],
                }
            )
        _make_memory_json(entries_data, path=project_dir)
        entries = inject_memory._collect_active_entries(
            json.loads((project_dir / ".ai-state" / "memory.json").read_text())["memories"]
        )
        result = inject_memory._build_tiered_output(entries, "_default")
        assert "more entries (use search to find them)" in result

    def test_no_footer_when_all_entries_fit(self, project_dir: Path):
        """No truncation footer when all entries fit within budget."""
        _make_memory_json(
            [
                {"category": "learnings", "key": "one", "value": "V", "importance": 7, "tags": []},
            ],
            path=project_dir,
        )
        entries = inject_memory._collect_active_entries(
            json.loads((project_dir / ".ai-state" / "memory.json").read_text())["memories"]
        )
        result = inject_memory._build_tiered_output(entries, "_default")
        assert "more entries" not in result

    def test_500_entries_within_budget(self, project_dir: Path):
        """Scaling test: 500 entries, output stays within budget."""
        entries_data = []
        for cat in ["learnings", "project", "user", "tools", "assistant"]:
            for i in range(100):
                entries_data.append(
                    {
                        "category": cat,
                        "key": f"{cat}_{i:03d}",
                        "value": f"Memory about {cat} topic {i}",
                        "summary": f"{cat} topic {i}",
                        "importance": 8 if i < 30 else 5,
                        "tags": ["t1"],
                    }
                )
        _make_memory_json(entries_data, path=project_dir)
        entries = inject_memory._collect_active_entries(
            json.loads((project_dir / ".ai-state" / "memory.json").read_text())["memories"]
        )
        result = inject_memory._build_tiered_output(entries, "_default")
        # Body must be within budget (footer may add a bit extra)
        body_without_footer = result.split("\n\n... and")[0]
        assert len(body_without_footer) <= inject_memory.MAX_INJECT_CHARS


# -- Lock tests ---------------------------------------------------------------


class TestLocking:
    def test_lock_sh_acquired_on_read(self, project_dir: Path):
        """Verify LOCK_SH is acquired when reading memory.json."""
        _make_memory_json(
            [{"category": "learnings", "key": "a", "value": "V", "importance": 7, "tags": []}],
            path=project_dir,
        )
        memory_path = project_dir / ".ai-state" / "memory.json"

        with patch.object(inject_memory.fcntl, "flock") as mock_flock:
            data = inject_memory._read_with_lock(memory_path)

        assert data is not None
        # LOCK_SH should have been called
        lock_calls = [
            call
            for call in mock_flock.call_args_list
            if len(call.args) >= 2 and call.args[1] == inject_memory.fcntl.LOCK_SH
        ]
        assert len(lock_calls) == 1, "Expected exactly one LOCK_SH call"


# -- Graceful degradation tests -----------------------------------------------


class TestGracefulDegradation:
    def test_missing_memory_json_returns_none(self, project_dir: Path):
        """No memory.json -> _read_with_lock returns None."""
        result = inject_memory._read_with_lock(project_dir / ".ai-state" / "memory.json")
        assert result is None

    def test_corrupt_memory_json_returns_none(self, project_dir: Path):
        """Corrupt JSON file -> _read_with_lock returns None."""
        ai_state = project_dir / ".ai-state"
        ai_state.mkdir(parents=True, exist_ok=True)
        (ai_state / "memory.json").write_text("not valid json{", encoding="utf-8")
        result = inject_memory._read_with_lock(ai_state / "memory.json")
        assert result is None

    def test_empty_memories_produces_no_output(self, project_dir: Path):
        """Empty memories dict -> empty entries list."""
        entries = inject_memory._collect_active_entries({})
        assert entries == []

    def test_lock_failure_still_reads(self, project_dir: Path):
        """If lock file cannot be created, read proceeds anyway."""
        _make_memory_json(
            [{"category": "learnings", "key": "a", "value": "V", "importance": 7, "tags": []}],
            path=project_dir,
        )
        memory_path = project_dir / ".ai-state" / "memory.json"

        # Simulate lock creation failure
        with patch.object(Path, "touch", side_effect=OSError("Permission denied")):
            data = inject_memory._read_with_lock(memory_path)

        assert data is not None
        assert "memories" in data


# -- Agent type resolution tests ----------------------------------------------


class TestAgentTypeResolution:
    def test_explicit_agent_type(self):
        """Explicit agent_type in payload is used directly."""
        result = inject_memory._resolve_agent_type({"agent_type": "implementer"})
        assert result == "implementer"

    def test_agent_type_from_description(self):
        """Agent type derived from description when agent_type not set."""
        result = inject_memory._resolve_agent_type(
            {
                "description": "You are a systems-architect analyzing the codebase",
            }
        )
        assert result == "systems-architect"

    def test_unknown_agent_type_returns_default(self):
        """Unknown agent type returns _default."""
        result = inject_memory._resolve_agent_type({"agent_type": "custom-agent"})
        assert result == "_default"

    def test_empty_payload_returns_default(self):
        """Empty payload returns _default."""
        result = inject_memory._resolve_agent_type({})
        assert result == "_default"
