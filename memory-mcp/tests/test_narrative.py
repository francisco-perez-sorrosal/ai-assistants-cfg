"""Tests for timeline and session narrative formatters."""

from __future__ import annotations

from memory_mcp.narrative import (
    NO_OBSERVATIONS_MESSAGE,
    build_session_narrative,
    build_timeline,
)

# -- Helpers ------------------------------------------------------------------


def _make_obs(
    *,
    timestamp: str = "2026-04-03T14:30:00Z",
    session_id: str = "sess-1",
    agent_type: str = "implementer",
    agent_id: str = "agent-1",
    project: str = "praxion",
    event_type: str = "tool_use",
    tool_name: str | None = "Write",
    file_paths: list[str] | None = None,
    outcome: str | None = "success",
    classification: str | None = "implementation",
    metadata: dict | None = None,
) -> dict:
    """Create an observation dict with sensible defaults."""
    return {
        "timestamp": timestamp,
        "session_id": session_id,
        "agent_type": agent_type,
        "agent_id": agent_id,
        "project": project,
        "event_type": event_type,
        "tool_name": tool_name,
        "file_paths": file_paths or [],
        "outcome": outcome,
        "classification": classification,
        "metadata": metadata or {},
    }


# -- build_timeline -----------------------------------------------------------


class TestBuildTimeline:
    def test_empty_returns_message(self) -> None:
        result = build_timeline([])
        assert result == NO_OBSERVATIONS_MESSAGE

    def test_single_event(self) -> None:
        obs = _make_obs(
            timestamp="2026-04-03T14:30:00Z",
            agent_type="implementer",
            tool_name="Write",
            outcome="success",
            file_paths=["src/foo.py"],
        )
        result = build_timeline([obs])
        assert "## 2026-04-03" in result
        assert "14:30" in result
        assert "[implementer]" in result
        assert "Write" in result
        assert "-> success" in result
        assert "(src/foo.py)" in result

    def test_grouped_by_date(self) -> None:
        obs1 = _make_obs(timestamp="2026-04-01T10:00:00Z", tool_name="Read")
        obs2 = _make_obs(timestamp="2026-04-02T11:00:00Z", tool_name="Write")
        obs3 = _make_obs(timestamp="2026-04-01T12:00:00Z", tool_name="Edit")

        result = build_timeline([obs1, obs2, obs3])
        # Both dates should appear as headings
        assert "## 2026-04-01" in result
        assert "## 2026-04-02" in result
        # April 1 heading should come before April 2
        idx_apr1 = result.index("## 2026-04-01")
        idx_apr2 = result.index("## 2026-04-02")
        assert idx_apr1 < idx_apr2

    def test_format_line_structure(self) -> None:
        """Verify the HH:MM [agent] tool -> outcome (files) format."""
        obs = _make_obs(
            timestamp="2026-04-03T09:15:00Z",
            agent_type="test-engineer",
            tool_name="Bash",
            outcome="failure",
            file_paths=["tests/test_foo.py", "tests/test_bar.py"],
        )
        result = build_timeline([obs])
        # Should contain the formatted line
        assert (
            "09:15 [test-engineer] Bash -> failure (tests/test_foo.py, tests/test_bar.py)" in result
        )

    def test_lifecycle_event_without_tool(self) -> None:
        """Lifecycle events (no tool_name) should use event_type as action."""
        obs = _make_obs(
            tool_name=None,
            event_type="session_start",
            outcome=None,
            classification=None,
        )
        result = build_timeline([obs])
        assert "session_start" in result

    def test_file_paths_truncated_at_three(self) -> None:
        obs = _make_obs(
            file_paths=["a.py", "b.py", "c.py", "d.py", "e.py"],
        )
        result = build_timeline([obs])
        assert "a.py, b.py, c.py" in result
        assert "+2 more" in result

    def test_query_description_header(self) -> None:
        obs = _make_obs()
        result = build_timeline([obs], query_description="last 24 hours")
        assert "# Timeline: last 24 hours" in result

    def test_chronological_within_date(self) -> None:
        """Within a date group, entries preserve input order."""
        obs1 = _make_obs(timestamp="2026-04-03T08:00:00Z", tool_name="Read")
        obs2 = _make_obs(timestamp="2026-04-03T09:00:00Z", tool_name="Write")
        result = build_timeline([obs1, obs2])
        idx_read = result.index("Read")
        idx_write = result.index("Write")
        assert idx_read < idx_write

    def test_multiple_agents(self) -> None:
        obs1 = _make_obs(agent_type="implementer", tool_name="Write")
        obs2 = _make_obs(agent_type="test-engineer", tool_name="Bash")
        result = build_timeline([obs1, obs2])
        assert "[implementer]" in result
        assert "[test-engineer]" in result


# -- build_session_narrative ---------------------------------------------------


class TestBuildSessionNarrative:
    def test_empty_returns_message(self) -> None:
        result = build_session_narrative([])
        assert result == NO_OBSERVATIONS_MESSAGE

    def test_all_sections_present(self) -> None:
        obs = _make_obs()
        result = build_session_narrative([obs])
        assert "## What Was Done" in result
        assert "## Files Touched" in result
        assert "## Decisions Made" in result
        assert "## Outcome" in result

    def test_what_was_done_groups_by_classification(self) -> None:
        obs1 = _make_obs(classification="implementation")
        obs2 = _make_obs(classification="implementation")
        obs3 = _make_obs(classification="test")
        result = build_session_narrative([obs1, obs2, obs3])
        assert "**implementation** (2):" in result
        assert "**test** (1):" in result

    def test_files_touched_deduplicated(self) -> None:
        obs1 = _make_obs(file_paths=["src/foo.py", "src/bar.py"])
        obs2 = _make_obs(file_paths=["src/foo.py", "src/baz.py"])
        result = build_session_narrative([obs1, obs2])
        # foo.py should appear exactly once
        assert result.count("`src/foo.py`") == 1
        assert "`src/bar.py`" in result
        assert "`src/baz.py`" in result

    def test_files_touched_empty(self) -> None:
        obs = _make_obs(file_paths=[])
        result = build_session_narrative([obs])
        assert "No file paths recorded." in result

    def test_decisions_extracted(self) -> None:
        obs1 = _make_obs(classification="implementation")
        obs2 = _make_obs(
            classification="decision",
            file_paths=[".ai-state/decisions/001-foo.md"],
            timestamp="2026-04-03T15:00:00Z",
        )
        result = build_session_narrative([obs1, obs2])
        # Decision section should list the decision file
        assert ".ai-state/decisions/001-foo.md" in result

    def test_decisions_empty(self) -> None:
        obs = _make_obs(classification="implementation")
        result = build_session_narrative([obs])
        assert "No decisions recorded." in result

    def test_outcome_counts(self) -> None:
        obs1 = _make_obs(outcome="success")
        obs2 = _make_obs(outcome="success")
        obs3 = _make_obs(outcome="failure")
        obs4 = _make_obs(outcome=None)
        result = build_session_narrative([obs1, obs2, obs3, obs4])
        assert "4 total events" in result
        assert "2 succeeded" in result
        assert "1 failed" in result
        assert "1 without outcome" in result

    def test_multiple_agents_in_narrative(self) -> None:
        obs1 = _make_obs(agent_type="implementer", classification="implementation")
        obs2 = _make_obs(agent_type="test-engineer", classification="test")
        result = build_session_narrative([obs1, obs2])
        # Both classifications should appear
        assert "**implementation**" in result
        assert "**test**" in result

    def test_what_was_done_uses_event_type_fallback(self) -> None:
        """When classification is None, event_type is used for grouping."""
        obs = _make_obs(classification=None, event_type="session_start")
        result = build_session_narrative([obs])
        assert "**session_start**" in result

    def test_narrative_header(self) -> None:
        obs = _make_obs()
        result = build_session_narrative([obs])
        assert result.startswith("# Session Narrative")
