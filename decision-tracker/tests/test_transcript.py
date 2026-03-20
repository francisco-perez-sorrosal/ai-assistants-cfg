"""Tests for decision_tracker.transcript — session JSONL parsing."""

from __future__ import annotations

import json
from pathlib import Path

from decision_tracker.transcript import get_last_commit_timestamp, read_transcript

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_jsonl(path: Path, entries: list[dict]) -> Path:
    """Write a list of dicts as JSONL lines to *path*."""
    path.write_text(
        "\n".join(json.dumps(e) for e in entries) + "\n",
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------------------
# read_transcript tests
# ---------------------------------------------------------------------------


class TestReadTranscript:
    def test_read_user_and_assistant(self, tmp_path: Path):
        session = tmp_path / "session.jsonl"
        _write_jsonl(
            session,
            [
                {"type": "user", "content": "Hello from user"},
                {
                    "type": "assistant",
                    "content": [{"type": "text", "text": "Hello from assistant"}],
                },
            ],
        )
        result = read_transcript(session)
        assert "Hello from user" in result
        assert "Hello from assistant" in result

    def test_skip_sidechain_and_meta(self, tmp_path: Path):
        session = tmp_path / "session.jsonl"
        _write_jsonl(
            session,
            [
                {"type": "user", "content": "visible", "isSidechain": False},
                {"type": "user", "content": "sidechain msg", "isSidechain": True},
                {
                    "type": "assistant",
                    "content": [{"type": "text", "text": "meta msg"}],
                    "isMeta": True,
                },
                {"type": "user", "content": "also visible"},
            ],
        )
        result = read_transcript(session)
        assert "visible" in result
        assert "also visible" in result
        assert "sidechain msg" not in result
        assert "meta msg" not in result

    def test_tool_use_placeholder(self, tmp_path: Path):
        session = tmp_path / "session.jsonl"
        _write_jsonl(
            session,
            [
                {
                    "type": "assistant",
                    "content": [
                        {"type": "tool_use", "name": "Read", "id": "t1", "input": {}},
                    ],
                },
            ],
        )
        result = read_transcript(session)
        assert "[tool: Read]" in result

    def test_skip_thinking_blocks(self, tmp_path: Path):
        session = tmp_path / "session.jsonl"
        _write_jsonl(
            session,
            [
                {
                    "type": "assistant",
                    "content": [
                        {"type": "thinking", "text": "internal reasoning"},
                        {"type": "text", "text": "visible reply"},
                    ],
                },
            ],
        )
        result = read_transcript(session)
        assert "internal reasoning" not in result
        assert "visible reply" in result

    def test_timestamp_filtering(self, tmp_path: Path):
        session = tmp_path / "session.jsonl"
        _write_jsonl(
            session,
            [
                {"type": "user", "content": "first", "timestamp": "2026-01-01T00:00:00Z"},
                {"type": "user", "content": "second", "timestamp": "2026-01-02T00:00:00Z"},
                {"type": "user", "content": "third", "timestamp": "2026-01-03T00:00:00Z"},
            ],
        )
        result = read_transcript(session, since_timestamp="2026-01-02T00:00:00Z")
        assert "first" not in result
        assert "second" in result
        assert "third" in result

    def test_truncate_large_turns(self, tmp_path: Path):
        session = tmp_path / "session.jsonl"
        long_text = "A" * 3000
        _write_jsonl(
            session,
            [
                {
                    "type": "assistant",
                    "content": [{"type": "text", "text": long_text}],
                },
            ],
        )
        result = read_transcript(session)
        assert "[truncated]" in result
        # The truncated output should contain the first 200 chars + " [truncated]"
        assert result.strip() == "A" * 200 + " [truncated]"

    def test_empty_file_returns_empty_string(self, tmp_path: Path):
        session = tmp_path / "session.jsonl"
        session.write_text("", encoding="utf-8")
        assert read_transcript(session) == ""

    def test_invalid_json_lines_skipped(self, tmp_path: Path):
        session = tmp_path / "session.jsonl"
        lines = [
            json.dumps({"type": "user", "content": "good line"}),
            "this is not json {{{",
            json.dumps({"type": "user", "content": "another good line"}),
        ]
        session.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = read_transcript(session)
        assert "good line" in result
        assert "another good line" in result

    def test_user_tool_result_skipped(self, tmp_path: Path):
        session = tmp_path / "session.jsonl"
        _write_jsonl(
            session,
            [
                {
                    "type": "user",
                    "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "result"}],
                },
                {"type": "user", "content": "normal message"},
            ],
        )
        result = read_transcript(session)
        assert "tool_result" not in result
        assert "normal message" in result


# ---------------------------------------------------------------------------
# get_last_commit_timestamp tests
# ---------------------------------------------------------------------------


class TestGetLastCommitTimestamp:
    def test_found(self, tmp_path: Path):
        decisions = tmp_path / "decisions.jsonl"
        _write_jsonl(
            decisions,
            [
                {"session_id": "sess-1", "timestamp": "2026-01-01T00:00:00Z", "decision": "A"},
                {"session_id": "sess-2", "timestamp": "2026-01-02T00:00:00Z", "decision": "B"},
                {"session_id": "sess-1", "timestamp": "2026-01-03T00:00:00Z", "decision": "C"},
            ],
        )
        result = get_last_commit_timestamp(decisions, "sess-1")
        assert result == "2026-01-03T00:00:00Z"

    def test_not_found(self, tmp_path: Path):
        decisions = tmp_path / "decisions.jsonl"
        _write_jsonl(
            decisions,
            [
                {"session_id": "sess-2", "timestamp": "2026-01-01T00:00:00Z", "decision": "A"},
            ],
        )
        result = get_last_commit_timestamp(decisions, "sess-1")
        assert result is None

    def test_no_file(self, tmp_path: Path):
        decisions = tmp_path / "nonexistent.jsonl"
        result = get_last_commit_timestamp(decisions, "sess-1")
        assert result is None
