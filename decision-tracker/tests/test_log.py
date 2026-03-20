"""Tests for decision_tracker.log — JSONL read/write operations."""

from __future__ import annotations

import json
from pathlib import Path

from decision_tracker.log import append_decision, read_all, read_recent
from decision_tracker.schema import Decision

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = {
    "status": "documented",
    "category": "implementation",
    "decision": "Use dict lookup",
    "made_by": "agent",
    "source": "agent",
}


def _make_decision(**overrides: object) -> Decision:
    """Create a Decision with sane defaults, allowing field overrides."""
    fields = {**REQUIRED_FIELDS, **overrides}
    return Decision(**fields)


# ---------------------------------------------------------------------------
# append_decision
# ---------------------------------------------------------------------------


class TestAppendCreatesFile:
    def test_creates_file_with_one_valid_json_line(self, tmp_path: Path):
        log_path = tmp_path / "decisions.jsonl"
        decision = _make_decision()

        append_decision(log_path, decision)

        assert log_path.exists()
        lines = log_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["decision"] == "Use dict lookup"


class TestAppendMultiple:
    def test_multiple_appends_produce_parseable_lines(self, tmp_path: Path):
        log_path = tmp_path / "decisions.jsonl"
        count = 5

        for i in range(count):
            append_decision(log_path, _make_decision(decision=f"Decision {i}"))

        lines = log_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == count
        for i, line in enumerate(lines):
            parsed = json.loads(line)
            assert parsed["decision"] == f"Decision {i}"


class TestAppendCreatesDirectory:
    def test_creates_parent_directories(self, tmp_path: Path):
        log_path = tmp_path / "deep" / "nested" / "dir" / "decisions.jsonl"

        append_decision(log_path, _make_decision())

        assert log_path.exists()
        parsed = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
        assert parsed["decision"] == "Use dict lookup"


# ---------------------------------------------------------------------------
# read_recent
# ---------------------------------------------------------------------------


class TestReadRecentReturnsLastN:
    def test_returns_last_n_entries(self, tmp_path: Path):
        log_path = tmp_path / "decisions.jsonl"
        total = 60
        requested = 50

        for i in range(total):
            append_decision(log_path, _make_decision(decision=f"Decision {i}"))

        results = read_recent(log_path, count=requested)

        assert len(results) == requested
        # First returned entry should be decision index (total - requested)
        assert results[0].decision == f"Decision {total - requested}"
        assert results[-1].decision == f"Decision {total - 1}"


class TestReadRecentEmptyFile:
    def test_returns_empty_list(self, tmp_path: Path):
        log_path = tmp_path / "decisions.jsonl"
        log_path.write_text("", encoding="utf-8")

        assert read_recent(log_path) == []


class TestReadRecentNonexistentFile:
    def test_returns_empty_list(self, tmp_path: Path):
        log_path = tmp_path / "nonexistent.jsonl"

        assert read_recent(log_path) == []


class TestReadRecentSkipsInvalidLines:
    def test_only_valid_lines_parsed(self, tmp_path: Path):
        log_path = tmp_path / "decisions.jsonl"
        valid = _make_decision(decision="Valid entry")
        valid_json = valid.model_dump_json(exclude_none=True)

        content = (
            "\n".join(
                [
                    valid_json,
                    "this is not json",
                    '{"bad": "schema"}',
                    valid_json,
                ]
            )
            + "\n"
        )
        log_path.write_text(content, encoding="utf-8")

        results = read_recent(log_path)

        assert len(results) == 2
        assert all(r.decision == "Valid entry" for r in results)


# ---------------------------------------------------------------------------
# read_all
# ---------------------------------------------------------------------------


class TestReadAll:
    def test_reads_complete_file(self, tmp_path: Path):
        log_path = tmp_path / "decisions.jsonl"
        total = 75

        for i in range(total):
            append_decision(log_path, _make_decision(decision=f"Decision {i}"))

        results = read_all(log_path)

        assert len(results) == total
        assert results[0].decision == "Decision 0"
        assert results[-1].decision == f"Decision {total - 1}"
