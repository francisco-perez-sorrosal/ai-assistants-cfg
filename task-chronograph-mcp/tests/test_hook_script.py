"""Tests for the Claude Code hook script at .claude-plugin/hooks/send_event.py."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import the hook script via importlib (it is outside the package)
# ---------------------------------------------------------------------------

HOOK_SCRIPT_PATH = (
    Path(__file__).resolve().parents[2] / ".claude-plugin" / "hooks" / "send_event.py"
)


@pytest.fixture
def build_events():
    """Load the _build_events function from the hook script."""
    spec = importlib.util.spec_from_file_location("send_event", HOOK_SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._build_events


# ---------------------------------------------------------------------------
# _build_events: SubagentStart
# ---------------------------------------------------------------------------


class TestBuildEventsSubagentStart:
    def test_subagent_start_produces_event_and_interaction(self, build_events):
        payload = {
            "hook_event_name": "SubagentStart",
            "agent_type": "i-am:researcher",
            "session_id": "sess-001",
            "agent_id": "agent-001",
        }
        events, interactions = build_events(payload)
        assert len(events) == 1
        event = events[0]
        assert event["event_type"] == "agent_start"
        assert event["agent_type"] == "i-am:researcher"
        assert event["session_id"] == "sess-001"
        assert event["agent_id"] == "agent-001"
        assert event["parent_session_id"] == "sess-001"
        assert "started" in event["message"]

        assert len(interactions) == 1
        ix = interactions[0]
        assert ix["source"] == "main_agent"
        assert ix["target"] == "agent-001"
        assert ix["interaction_type"] == "delegation"
        assert "researcher" in ix["summary"]

    def test_subagent_start_missing_agent_type_falls_back_to_unknown(self, build_events):
        payload = {
            "hook_event_name": "SubagentStart",
            "session_id": "sess-001",
        }
        events, interactions = build_events(payload)
        assert len(events) == 1
        assert events[0]["agent_type"] == "unknown"
        assert "unknown" in events[0]["message"]
        assert len(interactions) == 1
        assert "unknown" in interactions[0]["summary"]

    def test_subagent_start_empty_type_falls_back_to_agent_id(self, build_events):
        payload = {
            "hook_event_name": "SubagentStart",
            "agent_id": "abc1234",
            "session_id": "sess-001",
        }
        events, interactions = build_events(payload)
        assert events[0]["agent_type"] == "abc1234"
        assert "abc1234" in events[0]["message"]
        assert "abc1234" in interactions[0]["summary"]

    def test_subagent_start_interaction_uses_agent_type_when_no_id(self, build_events):
        payload = {
            "hook_event_name": "SubagentStart",
            "agent_type": "i-am:researcher",
            "session_id": "sess-001",
        }
        events, interactions = build_events(payload)
        assert interactions[0]["target"] == "i-am:researcher"


# ---------------------------------------------------------------------------
# _build_events: SubagentStop
# ---------------------------------------------------------------------------


class TestBuildEventsSubagentStop:
    def test_subagent_stop_produces_event_and_interaction(self, build_events):
        payload = {
            "hook_event_name": "SubagentStop",
            "agent_type": "i-am:researcher",
            "session_id": "sess-001",
            "agent_id": "agent-001",
            "agent_transcript_path": "/tmp/transcript.md",
        }
        events, interactions = build_events(payload)
        assert len(events) == 1
        event = events[0]
        assert event["event_type"] == "agent_stop"
        assert event["agent_type"] == "i-am:researcher"
        assert event["parent_session_id"] == "sess-001"
        assert "stopped" in event["message"]
        assert event["metadata"]["agent_transcript_path"] == "/tmp/transcript.md"

        assert len(interactions) == 1
        ix = interactions[0]
        assert ix["source"] == "agent-001"
        assert ix["target"] == "main_agent"
        assert ix["interaction_type"] == "result"

    def test_subagent_stop_without_transcript(self, build_events):
        payload = {
            "hook_event_name": "SubagentStop",
            "agent_type": "i-am:architect",
            "session_id": "sess-002",
        }
        events, interactions = build_events(payload)
        assert len(events) == 1
        assert events[0]["event_type"] == "agent_stop"
        assert "metadata" not in events[0]
        assert len(interactions) == 1


# ---------------------------------------------------------------------------
# _build_events: PostToolUse — PROGRESS.md parsing
# ---------------------------------------------------------------------------


class TestBuildEventsPostToolUse:
    def test_write_to_progress_md_with_parseable_content(self, build_events):
        content = (
            "[2025-01-15T10:30:00Z] [researcher] "
            "Phase 2/5: context-inventory -- Scanning skills directory"
        )
        payload = {
            "hook_event_name": "PostToolUse",
            "session_id": "sess-001",
            "agent_id": "agent-001",
            "tool_input": {
                "file_path": "/project/.ai-work/PROGRESS.md",
                "content": content,
            },
        }
        events, interactions = build_events(payload)
        assert len(events) == 1
        event = events[0]
        assert event["event_type"] == "phase_transition"
        assert event["agent_type"] == "researcher"
        assert event["phase"] == 2
        assert event["total_phases"] == 5
        assert event["phase_name"] == "context-inventory"
        assert "Scanning skills directory" in event["message"]
        assert len(interactions) == 0

    def test_edit_to_progress_md_uses_new_string(self, build_events):
        new_string = (
            "[2025-01-15T10:35:00Z] [systems-architect] "
            "Phase 1/4: scope -- Reviewing architecture requirements"
        )
        payload = {
            "hook_event_name": "PostToolUse",
            "session_id": "sess-001",
            "tool_input": {
                "file_path": "/project/.ai-work/PROGRESS.md",
                "new_string": new_string,
            },
        }
        events, interactions = build_events(payload)
        assert len(events) == 1
        assert events[0]["agent_type"] == "systems-architect"
        assert events[0]["phase"] == 1
        assert events[0]["total_phases"] == 4

    def test_write_to_progress_md_unparseable_content(self, build_events):
        payload = {
            "hook_event_name": "PostToolUse",
            "session_id": "sess-001",
            "tool_input": {
                "file_path": "/project/.ai-work/PROGRESS.md",
                "content": "some random text",
            },
        }
        events, interactions = build_events(payload)
        assert len(events) == 1
        assert events[0]["event_type"] == "phase_transition"
        assert events[0]["agent_type"] == "unknown"

    def test_write_to_progress_md_no_content(self, build_events):
        payload = {
            "hook_event_name": "PostToolUse",
            "session_id": "sess-001",
            "tool_input": {"file_path": "/project/.ai-work/PROGRESS.md"},
        }
        events, interactions = build_events(payload)
        assert len(events) == 1
        assert events[0]["agent_type"] == "unknown"

    def test_progress_line_without_phase(self, build_events):
        content = "[2025-01-15T10:30:00Z] [researcher] Starting exploration"
        payload = {
            "hook_event_name": "PostToolUse",
            "session_id": "sess-001",
            "tool_input": {
                "file_path": "/project/.ai-work/PROGRESS.md",
                "content": content,
            },
        }
        events, interactions = build_events(payload)
        assert len(events) == 1
        assert events[0]["agent_type"] == "researcher"
        assert events[0]["phase"] == 0
        assert events[0]["total_phases"] == 0
        assert events[0]["phase_name"] == ""

    def test_write_to_other_file_returns_empty(self, build_events):
        payload = {
            "hook_event_name": "PostToolUse",
            "session_id": "sess-001",
            "tool_input": {"file_path": "/project/src/module.py"},
        }
        events, interactions = build_events(payload)
        assert events == []
        assert interactions == []

    def test_write_without_tool_input_returns_empty(self, build_events):
        payload = {
            "hook_event_name": "PostToolUse",
            "session_id": "sess-001",
        }
        events, interactions = build_events(payload)
        assert events == []
        assert interactions == []

    def test_multiline_content_parses_last_line(self, build_events):
        content = (
            "[2025-01-15T10:30:00Z] [researcher] Phase 1/5: scope -- Understanding request\n"
            "[2025-01-15T10:35:00Z] [researcher] Phase 2/5: inventory -- Cataloging artifacts\n"
        )
        payload = {
            "hook_event_name": "PostToolUse",
            "session_id": "sess-001",
            "tool_input": {
                "file_path": "/project/.ai-work/PROGRESS.md",
                "content": content,
            },
        }
        events, interactions = build_events(payload)
        assert len(events) == 1
        assert events[0]["phase"] == 2
        assert events[0]["phase_name"] == "inventory"

    def test_progress_line_with_hashtag_labels(self, build_events):
        content = (
            "[2025-01-15T10:30:00Z] [researcher] "
            "Phase 2/5: scope -- Scanning codebase #observability #feature=auth"
        )
        payload = {
            "hook_event_name": "PostToolUse",
            "session_id": "sess-001",
            "tool_input": {
                "file_path": "/project/.ai-work/PROGRESS.md",
                "content": content,
            },
        }
        events, interactions = build_events(payload)
        assert events[0]["message"] == "Scanning codebase"


# ---------------------------------------------------------------------------
# _build_events: Unknown hook
# ---------------------------------------------------------------------------


class TestBuildEventsUnknownHook:
    def test_unknown_hook_returns_empty_lists(self, build_events):
        payload = {"hook_event_name": "SomeUnknownHook", "session_id": "sess-001"}
        events, interactions = build_events(payload)
        assert events == []
        assert interactions == []

    def test_missing_hook_name_returns_empty_lists(self, build_events):
        payload = {"session_id": "sess-001"}
        events, interactions = build_events(payload)
        assert events == []
        assert interactions == []


# ---------------------------------------------------------------------------
# Hook script: exits 0 when server is unavailable
# ---------------------------------------------------------------------------


class TestHookScriptProcess:
    def test_exits_zero_when_server_unavailable(self):
        """Run the actual script via subprocess, piping valid JSON to stdin."""
        payload = json.dumps(
            {
                "hook_event_name": "SubagentStart",
                "agent_type": "researcher",
                "session_id": "sess-001",
            }
        )
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT_PATH)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=10,
            env={"CHRONOGRAPH_PORT": "19999", "PATH": ""},
        )
        assert result.returncode == 0

    def test_exits_zero_with_invalid_json(self):
        """Script should not crash even with bad input."""
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT_PATH)],
            input="not json at all",
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
