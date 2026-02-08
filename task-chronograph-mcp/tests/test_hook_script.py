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
def build_event():
    """Load the _build_event function from the hook script."""
    spec = importlib.util.spec_from_file_location("send_event", HOOK_SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._build_event


# ---------------------------------------------------------------------------
# _build_event: SubagentStart
# ---------------------------------------------------------------------------


class TestBuildEventSubagentStart:
    def test_subagent_start_maps_correctly(self, build_event):
        payload = {
            "hook_event_name": "SubagentStart",
            "agent_type": "i-am:researcher",
            "session_id": "sess-001",
            "agent_id": "agent-001",
        }
        event = build_event(payload)
        assert event is not None
        assert event["event_type"] == "agent_start"
        assert event["agent_type"] == "i-am:researcher"
        assert event["session_id"] == "sess-001"
        assert event["agent_id"] == "agent-001"
        assert event["parent_session_id"] == "sess-001"
        assert "started" in event["message"]

    def test_subagent_start_missing_agent_type(self, build_event):
        payload = {
            "hook_event_name": "SubagentStart",
            "session_id": "sess-001",
        }
        event = build_event(payload)
        assert event is not None
        assert event["agent_type"] == ""


# ---------------------------------------------------------------------------
# _build_event: SubagentStop
# ---------------------------------------------------------------------------


class TestBuildEventSubagentStop:
    def test_subagent_stop_maps_correctly(self, build_event):
        payload = {
            "hook_event_name": "SubagentStop",
            "agent_type": "i-am:researcher",
            "session_id": "sess-001",
            "agent_id": "agent-001",
            "agent_transcript_path": "/tmp/transcript.md",
        }
        event = build_event(payload)
        assert event is not None
        assert event["event_type"] == "agent_stop"
        assert event["agent_type"] == "i-am:researcher"
        assert event["parent_session_id"] == "sess-001"
        assert "stopped" in event["message"]
        assert event["metadata"]["agent_transcript_path"] == "/tmp/transcript.md"

    def test_subagent_stop_without_transcript(self, build_event):
        payload = {
            "hook_event_name": "SubagentStop",
            "agent_type": "i-am:architect",
            "session_id": "sess-002",
        }
        event = build_event(payload)
        assert event is not None
        assert event["event_type"] == "agent_stop"
        assert "metadata" not in event


# ---------------------------------------------------------------------------
# _build_event: PostToolUse
# ---------------------------------------------------------------------------


class TestBuildEventPostToolUse:
    def test_write_to_progress_md_is_phase_transition(self, build_event):
        payload = {
            "hook_event_name": "PostToolUse",
            "session_id": "sess-001",
            "tool_input": {"file_path": "/project/.ai-work/PROGRESS.md"},
        }
        event = build_event(payload)
        assert event is not None
        assert event["event_type"] == "phase_transition"
        assert event["metadata"]["file_path"] == "/project/.ai-work/PROGRESS.md"

    def test_write_to_other_file_is_tool_use(self, build_event):
        payload = {
            "hook_event_name": "PostToolUse",
            "session_id": "sess-001",
            "tool_input": {"file_path": "/project/src/module.py"},
        }
        event = build_event(payload)
        assert event is not None
        assert event["event_type"] == "tool_use"

    def test_write_without_tool_input(self, build_event):
        payload = {
            "hook_event_name": "PostToolUse",
            "session_id": "sess-001",
        }
        event = build_event(payload)
        assert event is not None
        assert event["event_type"] == "tool_use"


# ---------------------------------------------------------------------------
# _build_event: Unknown hook
# ---------------------------------------------------------------------------


class TestBuildEventUnknownHook:
    def test_unknown_hook_returns_none(self, build_event):
        payload = {"hook_event_name": "SomeUnknownHook", "session_id": "sess-001"}
        event = build_event(payload)
        assert event is None

    def test_missing_hook_name_returns_none(self, build_event):
        payload = {"session_id": "sess-001"}
        event = build_event(payload)
        assert event is None


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
