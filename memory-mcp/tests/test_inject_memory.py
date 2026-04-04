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


# -- ADR test helpers ---------------------------------------------------------

_SAMPLE_ADR_ROWS = [
    {
        "id": "dec-001",
        "title": "Use skill wrapper for context-hub",
        "status": "accepted",
        "category": "architectural",
        "date": "2026-03-31",
        "tags": "context-hub, skills",
        "summary": "Skill wrapper instead of MCP server",
    },
    {
        "id": "dec-002",
        "title": "OTel relay for telemetry",
        "status": "accepted",
        "category": "architectural",
        "date": "2026-03-31",
        "tags": "observability, otel",
        "summary": "Hooks POST events to chronograph",
    },
    {
        "id": "dec-003",
        "title": "Dual-layer memory architecture",
        "status": "proposed",
        "category": "architectural",
        "date": "2026-04-03",
        "tags": "memory, architecture",
        "summary": "Curated JSON plus append-only JSONL",
    },
]


def _make_decisions_index(rows: list[dict], *, path: Path) -> None:
    """Write a DECISIONS_INDEX.md file from a list of ADR row dicts."""
    decisions_dir = path / ".ai-state" / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Decisions Index\n",
        "Auto-generated from ADR frontmatter. Do not edit manually.",
        "Regenerate: `python scripts/regenerate_adr_index.py`\n",
        "| ID | Title | Status | Category | Date | Tags | Summary |",
        "|----|-------|--------|----------|------|------|---------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | {r['title']} | {r['status']} | "
            f"{r['category']} | {r['date']} | {r['tags']} | {r['summary']} |"
        )
    (decisions_dir / "DECISIONS_INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# -- ADR index parsing tests --------------------------------------------------


class TestADRIndexParsing:
    def test_parses_valid_index_rows(self, project_dir: Path):
        """Standard rows produce parsed dicts with correct fields."""
        _make_decisions_index(_SAMPLE_ADR_ROWS, path=project_dir)
        content = (project_dir / ".ai-state" / "decisions" / "DECISIONS_INDEX.md").read_text()
        rows = inject_memory._parse_index_rows(content)
        assert len(rows) == 3
        assert rows[0]["id"] == "dec-001"
        assert rows[0]["title"] == "Use skill wrapper for context-hub"
        assert rows[0]["status"] == "accepted"
        assert rows[2]["status"] == "proposed"

    def test_filters_superseded_and_rejected(self):
        """Rows with superseded or rejected status are excluded."""
        content = (
            "| ID | Title | Status | Category | Date | Tags | Summary |\n"
            "|----|-------|--------|----------|------|------|---------|  \n"
            "| dec-001 | A | superseded | arch | 2026-01-01 | t1 | S1 |\n"
            "| dec-002 | B | rejected | arch | 2026-01-01 | t2 | S2 |\n"
            "| dec-003 | C | accepted | arch | 2026-01-01 | t3 | S3 |\n"
        )
        rows = inject_memory._parse_index_rows(content)
        assert len(rows) == 1
        assert rows[0]["id"] == "dec-003"

    def test_keeps_accepted_and_proposed(self):
        """Both accepted and proposed rows pass the filter."""
        content = (
            "| ID | Title | Status | Category | Date | Tags | Summary |\n"
            "|----|-------|--------|----------|------|------|---------|  \n"
            "| dec-001 | A | accepted | arch | 2026-01-01 | t1 | S1 |\n"
            "| dec-002 | B | proposed | arch | 2026-01-01 | t2 | S2 |\n"
        )
        rows = inject_memory._parse_index_rows(content)
        assert len(rows) == 2
        statuses = {r["status"] for r in rows}
        assert statuses == {"accepted", "proposed"}

    def test_skips_malformed_rows(self):
        """Rows with wrong column count are silently skipped."""
        content = (
            "| ID | Title | Status | Category | Date | Tags | Summary |\n"
            "|----|-------|--------|----------|------|------|---------|  \n"
            "| dec-001 | A | accepted | arch | 2026-01-01 | t1 | S1 |\n"
            "| dec-002 | only-two-cols |\n"
            "| dec-003 | C | accepted | arch | 2026-01-01 | t3 | S3 |\n"
        )
        rows = inject_memory._parse_index_rows(content)
        assert len(rows) == 2

    def test_skips_header_and_separator_lines(self):
        """Header, separator, blank, and metadata lines are not parsed as data."""
        content = (
            "# Decisions Index\n"
            "\n"
            "Auto-generated from ADR frontmatter.\n"
            "Regenerate: `python scripts/regenerate_adr_index.py`\n"
            "\n"
            "| ID | Title | Status | Category | Date | Tags | Summary |\n"
            "|----|-------|--------|----------|------|------|---------|  \n"
            "| dec-001 | A | accepted | arch | 2026-01-01 | t1 | S1 |\n"
        )
        rows = inject_memory._parse_index_rows(content)
        assert len(rows) == 1

    def test_empty_index_returns_empty_list(self):
        """Index with only headers produces empty list."""
        content = (
            "| ID | Title | Status | Category | Date | Tags | Summary |\n"
            "|----|-------|--------|----------|------|------|---------|  \n"
        )
        rows = inject_memory._parse_index_rows(content)
        assert rows == []

    def test_status_filtering_is_case_insensitive(self):
        """Status comparison is case-insensitive."""
        content = (
            "| ID | Title | Status | Category | Date | Tags | Summary |\n"
            "|----|-------|--------|----------|------|------|---------|  \n"
            "| dec-001 | A | Accepted | arch | 2026-01-01 | t1 | S1 |\n"
            "| dec-002 | B | PROPOSED | arch | 2026-01-01 | t2 | S2 |\n"
        )
        rows = inject_memory._parse_index_rows(content)
        assert len(rows) == 2


# -- ADR output formatting tests ----------------------------------------------


class TestADROutput:
    def test_formats_entries_in_rich_semantic_format(self):
        """Output matches the rich semantic format with all fields."""
        rows = [_SAMPLE_ADR_ROWS[0]]
        parsed = [
            {
                "id": r["id"],
                "title": r["title"],
                "status": r["status"],
                "category": r["category"],
                "date": r["date"],
                "tags": r["tags"],
                "summary": r["summary"],
            }
            for r in rows
        ]
        result = inject_memory._build_adr_output(parsed, budget=2000)
        assert "**dec-001**" in result
        assert "Use skill wrapper for context-hub" in result
        assert "(accepted)" in result
        assert "Skill wrapper instead of MCP server" in result
        assert "[context-hub, skills]" in result

    def test_respects_budget(self):
        """Output does not exceed the given budget."""
        parsed = [
            {
                "id": r["id"],
                "title": r["title"],
                "status": r["status"],
                "category": r["category"],
                "date": r["date"],
                "tags": r["tags"],
                "summary": r["summary"],
            }
            for r in _SAMPLE_ADR_ROWS
        ]
        result = inject_memory._build_adr_output(parsed, budget=200)
        # Should fit at most 1 entry in 200 chars
        assert len(result) <= 200 + 100  # +100 for truncation footer

    def test_entries_trimmed_when_budget_tight(self):
        """With small budget, only as many entries as fit are included."""
        parsed = [
            {
                "id": f"dec-{i:03d}",
                "title": f"Decision {i}",
                "status": "accepted",
                "category": "architectural",
                "date": "2026-01-01",
                "tags": "tag1, tag2",
                "summary": f"Summary for decision {i} with some detail",
            }
            for i in range(20)
        ]
        result = inject_memory._build_adr_output(parsed, budget=500)
        line_count = len([line for line in result.split("\n") if line.startswith("- **")])
        assert line_count < 20

    def test_empty_rows_returns_empty_string(self):
        """Empty input produces empty string."""
        result = inject_memory._build_adr_output([], budget=2000)
        assert result == ""

    def test_truncation_footer_when_entries_dropped(self):
        """Footer indicates omitted count when entries are dropped."""
        parsed = [
            {
                "id": f"dec-{i:03d}",
                "title": f"Decision {i}",
                "status": "accepted",
                "category": "architectural",
                "date": "2026-01-01",
                "tags": "tag1",
                "summary": f"Summary {i}",
            }
            for i in range(30)
        ]
        result = inject_memory._build_adr_output(parsed, budget=500)
        assert "more decisions" in result


# -- ADR graceful degradation tests -------------------------------------------


class TestADRGracefulDegradation:
    def test_missing_decisions_dir_no_adr_section(self, project_dir: Path):
        """No .ai-state/decisions/ directory -> no ADR section, memory works."""
        _make_memory_json(
            [
                {
                    "category": "learnings",
                    "key": "a",
                    "value": "V",
                    "importance": 7,
                    "tags": [],
                }
            ],
            path=project_dir,
        )
        payload = json.dumps({"cwd": str(project_dir)}).encode()
        import io
        from io import StringIO

        with (
            patch("sys.stdin", io.TextIOWrapper(io.BytesIO(payload))),
            patch("sys.stdout", new_callable=StringIO) as mock_stdout,
        ):
            inject_memory.main()
        output_str = mock_stdout.getvalue()
        if output_str.strip():
            result = json.loads(output_str)
            ctx = result["hookSpecificOutput"]["additionalContext"]
            assert "Memory Context" in ctx
            assert "Decision Context" not in ctx

    def test_missing_index_file_no_adr_section(self, project_dir: Path):
        """Directory exists but no DECISIONS_INDEX.md -> no ADR section."""
        decisions_dir = project_dir / ".ai-state" / "decisions"
        decisions_dir.mkdir(parents=True, exist_ok=True)
        index_path = decisions_dir / "DECISIONS_INDEX.md"
        result = inject_memory._read_decisions_index(index_path)
        assert result is None

    def test_empty_index_file_no_adr_section(self, project_dir: Path):
        """Empty file -> returns None."""
        decisions_dir = project_dir / ".ai-state" / "decisions"
        decisions_dir.mkdir(parents=True, exist_ok=True)
        (decisions_dir / "DECISIONS_INDEX.md").write_text("", encoding="utf-8")
        result = inject_memory._read_decisions_index(decisions_dir / "DECISIONS_INDEX.md")
        assert result is None

    def test_memory_works_without_adrs(self, project_dir: Path):
        """Full memory output when no ADRs exist (backward compat)."""
        _make_memory_json(
            [
                {
                    "category": "learnings",
                    "key": "critical",
                    "value": "Critical info",
                    "importance": 9,
                    "tags": ["test"],
                }
            ],
            path=project_dir,
        )
        payload = json.dumps({"cwd": str(project_dir)}).encode()
        import io
        from io import StringIO

        with (
            patch("sys.stdin", io.TextIOWrapper(io.BytesIO(payload))),
            patch("sys.stdout", new_callable=StringIO) as mock_stdout,
        ):
            inject_memory.main()
        result = json.loads(mock_stdout.getvalue())
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "Memory Context" in ctx
        assert "critical" in ctx
        assert "Decision Context" not in ctx

    def test_adrs_work_without_memory(self, project_dir: Path):
        """ADR section present when memory.json is missing."""
        _make_decisions_index(_SAMPLE_ADR_ROWS, path=project_dir)
        # No memory.json created
        payload = json.dumps({"cwd": str(project_dir)}).encode()
        import io
        from io import StringIO

        with (
            patch("sys.stdin", io.TextIOWrapper(io.BytesIO(payload))),
            patch("sys.stdout", new_callable=StringIO) as mock_stdout,
        ):
            inject_memory.main()
        output_str = mock_stdout.getvalue()
        if output_str.strip():
            result = json.loads(output_str)
            ctx = result["hookSpecificOutput"]["additionalContext"]
            assert "Decision Context" in ctx
            assert "Memory Context" not in ctx


# -- ADR budget integration tests ---------------------------------------------


class TestADRBudgetIntegration:
    def test_both_sections_within_budget(self, project_dir: Path):
        """Combined memory + ADR output under MAX_INJECT_CHARS."""
        _make_memory_json(
            [
                {
                    "category": "learnings",
                    "key": "a",
                    "value": "V",
                    "importance": 7,
                    "tags": [],
                }
            ],
            path=project_dir,
        )
        _make_decisions_index(_SAMPLE_ADR_ROWS, path=project_dir)
        payload = json.dumps({"cwd": str(project_dir)}).encode()
        import io
        from io import StringIO

        with (
            patch("sys.stdin", io.TextIOWrapper(io.BytesIO(payload))),
            patch("sys.stdout", new_callable=StringIO) as mock_stdout,
        ):
            inject_memory.main()
        result = json.loads(mock_stdout.getvalue())
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert len(ctx) <= inject_memory.MAX_INJECT_CHARS + 200
        assert "Memory Context" in ctx
        assert "Decision Context" in ctx

    def test_adrs_trimmed_by_soft_cap(self):
        """When budget is ample but ADRs exceed soft cap, ADRs are trimmed."""
        parsed = [
            {
                "id": f"dec-{i:03d}",
                "title": f"Decision number {i} with a longer title",
                "status": "accepted",
                "category": "architectural",
                "date": "2026-01-01",
                "tags": "tag1, tag2, tag3",
                "summary": f"A detailed summary for decision {i} explaining the rationale",
            }
            for i in range(30)
        ]
        result = inject_memory._build_adr_output(parsed, budget=6000)
        # Soft cap is 2000, so should be trimmed despite 6000 budget
        assert len(result) <= inject_memory.ADR_SOFT_CAP + 100  # +100 for footer

    def test_adrs_trimmed_below_soft_cap_when_memory_large(self, project_dir: Path):
        """Large memory output pushes ADRs below soft cap."""
        # Create many high-importance memory entries to consume budget
        entries = [
            {
                "category": "learnings",
                "key": f"entry_{i:03d}",
                "value": f"Important learning about topic {i} in the project",
                "summary": f"Topic {i} learning summary",
                "importance": 8,
                "tags": ["t1", "t2"],
            }
            for i in range(200)
        ]
        _make_memory_json(entries, path=project_dir)
        _make_decisions_index(_SAMPLE_ADR_ROWS, path=project_dir)
        payload = json.dumps({"cwd": str(project_dir)}).encode()
        import io
        from io import StringIO

        with (
            patch("sys.stdin", io.TextIOWrapper(io.BytesIO(payload))),
            patch("sys.stdout", new_callable=StringIO) as mock_stdout,
        ):
            inject_memory.main()
        result = json.loads(mock_stdout.getvalue())
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert len(ctx) <= inject_memory.MAX_INJECT_CHARS + 200

    def test_no_adr_section_when_zero_remaining_budget(self):
        """When budget is zero, no ADR output is produced."""
        parsed = [_SAMPLE_ADR_ROWS[0]]
        result = inject_memory._build_adr_output(parsed, budget=0)
        assert result == ""

    def test_adr_output_with_ample_budget_includes_all(self):
        """When budget is ample and few ADRs, all are included."""
        parsed = [
            {
                "id": r["id"],
                "title": r["title"],
                "status": r["status"],
                "category": r["category"],
                "date": r["date"],
                "tags": r["tags"],
                "summary": r["summary"],
            }
            for r in _SAMPLE_ADR_ROWS
        ]
        result = inject_memory._build_adr_output(parsed, budget=6000)
        line_count = len([line for line in result.split("\n") if line.startswith("- **")])
        assert line_count == 3


# -- ADR end-to-end tests -----------------------------------------------------


class TestADREndToEnd:
    def test_both_memory_and_adrs_in_output(self, project_dir: Path):
        """Both sections present in final JSON output."""
        _make_memory_json(
            [
                {
                    "category": "learnings",
                    "key": "learn1",
                    "value": "A learning",
                    "importance": 7,
                    "tags": ["test"],
                }
            ],
            path=project_dir,
        )
        _make_decisions_index(_SAMPLE_ADR_ROWS, path=project_dir)
        payload = json.dumps({"cwd": str(project_dir)}).encode()
        import io
        from io import StringIO

        with (
            patch("sys.stdin", io.TextIOWrapper(io.BytesIO(payload))),
            patch("sys.stdout", new_callable=StringIO) as mock_stdout,
        ):
            inject_memory.main()
        result = json.loads(mock_stdout.getvalue())
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "## Memory Context (auto-injected)" in ctx
        assert "## Decision Context (auto-injected)" in ctx
        assert "dec-001" in ctx

    def test_adr_section_header_format(self, project_dir: Path):
        """Output contains the correct Decision Context header."""
        _make_decisions_index(_SAMPLE_ADR_ROWS[:1], path=project_dir)
        payload = json.dumps({"cwd": str(project_dir)}).encode()
        import io
        from io import StringIO

        with (
            patch("sys.stdin", io.TextIOWrapper(io.BytesIO(payload))),
            patch("sys.stdout", new_callable=StringIO) as mock_stdout,
        ):
            inject_memory.main()
        result = json.loads(mock_stdout.getvalue())
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "## Decision Context (auto-injected)" in ctx

    def test_hook_event_name_present(self, project_dir: Path):
        """Output JSON includes hookEventName: SubagentStart."""
        _make_decisions_index(_SAMPLE_ADR_ROWS[:1], path=project_dir)
        payload = json.dumps({"cwd": str(project_dir)}).encode()
        import io
        from io import StringIO

        with (
            patch("sys.stdin", io.TextIOWrapper(io.BytesIO(payload))),
            patch("sys.stdout", new_callable=StringIO) as mock_stdout,
        ):
            inject_memory.main()
        result = json.loads(mock_stdout.getvalue())
        assert result["hookSpecificOutput"]["hookEventName"] == "SubagentStart"

    def test_decisions_appear_before_memory_in_output(self, project_dir: Path):
        """ADR section appears before memory section in the injected context."""
        _make_memory_json(
            [
                {
                    "category": "learnings",
                    "key": "a",
                    "value": "V",
                    "importance": 7,
                    "tags": [],
                }
            ],
            path=project_dir,
        )
        _make_decisions_index(_SAMPLE_ADR_ROWS[:1], path=project_dir)
        payload = json.dumps({"cwd": str(project_dir)}).encode()
        import io
        from io import StringIO

        with (
            patch("sys.stdin", io.TextIOWrapper(io.BytesIO(payload))),
            patch("sys.stdout", new_callable=StringIO) as mock_stdout,
        ):
            inject_memory.main()
        result = json.loads(mock_stdout.getvalue())
        ctx = result["hookSpecificOutput"]["additionalContext"]
        dec_pos = ctx.find("## Decision Context")
        mem_pos = ctx.find("## Memory Context")
        assert dec_pos < mem_pos, "Decisions must appear before memory"

    def test_total_output_within_budget_with_both_sources(self, project_dir: Path):
        """Combined output including headers stays within MAX_INJECT_CHARS."""
        # Many memory entries to pressure the budget
        entries = [
            {
                "category": "learnings",
                "key": f"entry_{i:03d}",
                "value": f"Important learning about topic {i} in the project",
                "summary": f"Topic {i} learning summary",
                "importance": 8,
                "tags": ["t1", "t2"],
            }
            for i in range(200)
        ]
        _make_memory_json(entries, path=project_dir)
        _make_decisions_index(_SAMPLE_ADR_ROWS, path=project_dir)
        payload = json.dumps({"cwd": str(project_dir)}).encode()
        import io
        from io import StringIO

        with (
            patch("sys.stdin", io.TextIOWrapper(io.BytesIO(payload))),
            patch("sys.stdout", new_callable=StringIO) as mock_stdout,
        ):
            inject_memory.main()
        result = json.loads(mock_stdout.getvalue())
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert len(ctx) <= inject_memory.MAX_INJECT_CHARS, (
            f"Total output {len(ctx)} exceeds budget {inject_memory.MAX_INJECT_CHARS}"
        )

    def test_adrs_get_priority_over_memory(self, project_dir: Path):
        """When budget is tight, ADRs are preserved and memory is trimmed."""
        # Fill memory with many high-importance entries
        entries = [
            {
                "category": "learnings",
                "key": f"entry_{i:03d}",
                "value": f"Important learning about topic {i} in the project",
                "summary": f"Topic {i} learning summary text here",
                "importance": 9,
                "tags": ["t1", "t2"],
            }
            for i in range(500)
        ]
        _make_memory_json(entries, path=project_dir)
        _make_decisions_index(_SAMPLE_ADR_ROWS, path=project_dir)
        payload = json.dumps({"cwd": str(project_dir)}).encode()
        import io
        from io import StringIO

        with (
            patch("sys.stdin", io.TextIOWrapper(io.BytesIO(payload))),
            patch("sys.stdout", new_callable=StringIO) as mock_stdout,
        ):
            inject_memory.main()
        result = json.loads(mock_stdout.getvalue())
        ctx = result["hookSpecificOutput"]["additionalContext"]
        # ADRs must be present even when memory is huge
        assert "Decision Context" in ctx
        assert "dec-001" in ctx
