"""Tests for hooks/_hook_utils.py — shared hook utilities.

Covers:
  - is_disabled(): per-project opt-out flag parsing for the three hook
    categories (memory injection, memory gate, observability).
  - End-to-end integration: each hook returns exit 0 without producing
    output when its corresponding flag is set, and proceeds normally when
    it is not set. Confirms the wiring between `_hook_utils.is_disabled`
    and each consumer hook's early-exit path.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent


@pytest.fixture(autouse=True)
def _clear_praxion_env(monkeypatch):
    """Each test starts with no PRAXION_* env vars set."""
    for key in (
        "PRAXION_DISABLE_MEMORY_INJECTION",
        "PRAXION_DISABLE_MEMORY_GATE",
        "PRAXION_DISABLE_OBSERVABILITY",
        "PRAXION_DISABLE_MEMORY_MCP",
    ):
        monkeypatch.delenv(key, raising=False)


def _import_hook_utils():
    """Reload `_hook_utils` so tests pick up current env state."""
    sys.path.insert(0, str(HOOKS_DIR))
    import importlib

    import _hook_utils

    return importlib.reload(_hook_utils)


def test_is_disabled_false_when_unset(monkeypatch):
    hu = _import_hook_utils()
    assert hu.is_disabled("PRAXION_DISABLE_MEMORY_INJECTION") is False


@pytest.mark.parametrize("truthy", ["1", "true", "TRUE", "Yes", "  yes  "])
def test_is_disabled_true_for_truthy_values(monkeypatch, truthy):
    monkeypatch.setenv("PRAXION_DISABLE_MEMORY_INJECTION", truthy)
    hu = _import_hook_utils()
    assert hu.is_disabled("PRAXION_DISABLE_MEMORY_INJECTION") is True


@pytest.mark.parametrize("falsy", ["", "0", "false", "no", "off", "disabled"])
def test_is_disabled_false_for_falsy_values(monkeypatch, falsy):
    monkeypatch.setenv("PRAXION_DISABLE_MEMORY_INJECTION", falsy)
    hu = _import_hook_utils()
    assert hu.is_disabled("PRAXION_DISABLE_MEMORY_INJECTION") is False


def test_flag_names_are_distinct():
    hu = _import_hook_utils()
    names = {
        hu.DISABLE_MEMORY_INJECTION,
        hu.DISABLE_MEMORY_GATE,
        hu.DISABLE_OBSERVABILITY,
        hu.DISABLE_MEMORY_MCP,
    }
    assert len(names) == 4
    assert all(n.startswith("PRAXION_DISABLE_") for n in names)


# -- Integration: each hook short-circuits when its flag is set ---------------


def _run_hook(
    script_name: str, payload: dict, env_extra: dict
) -> subprocess.CompletedProcess:
    env = {**os.environ, **env_extra}
    return subprocess.run(
        [sys.executable, str(HOOKS_DIR / script_name)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


_MINIMAL_PAYLOAD = {
    "cwd": "/tmp",
    "hook_event_name": "SessionStart",
    "session_id": "test-session",
    "transcript_path": "/dev/null",
    "tool_name": "Bash",
    "tool_input": {"command": "echo hi"},
    "tool_response": {},
}


@pytest.mark.parametrize(
    "script,flag",
    [
        ("inject_memory.py", "PRAXION_DISABLE_MEMORY_INJECTION"),
        ("memory_gate.py", "PRAXION_DISABLE_MEMORY_GATE"),
        ("memory_gate.py", "PRAXION_DISABLE_MEMORY_MCP"),
        ("validate_memory.py", "PRAXION_DISABLE_MEMORY_GATE"),
        ("validate_memory.py", "PRAXION_DISABLE_MEMORY_MCP"),
        ("send_event.py", "PRAXION_DISABLE_OBSERVABILITY"),
        ("capture_session.py", "PRAXION_DISABLE_OBSERVABILITY"),
        ("capture_memory.py", "PRAXION_DISABLE_OBSERVABILITY"),
    ],
)
def test_hook_exits_silently_when_disabled(script, flag):
    """With the flag set, each hook must exit 0 and emit no output."""
    result = _run_hook(script, _MINIMAL_PAYLOAD, {flag: "1"})
    assert result.returncode == 0, (
        f"{script} exited {result.returncode}: {result.stderr}"
    )
    assert result.stdout == "", (
        f"{script} emitted stdout when disabled: {result.stdout!r}"
    )
    assert result.stderr == "", (
        f"{script} emitted stderr when disabled: {result.stderr!r}"
    )


# -- inject_memory.py: MCP flag emits the disabled notice (not silent) -------


def test_inject_memory_emits_disabled_notice_under_mcp_flag():
    """Under PRAXION_DISABLE_MEMORY_MCP, inject_memory.py emits ONLY a disabled
    notice as additionalContext.

    This is the novel behavior that distinguishes DISABLE_MEMORY_MCP from
    DISABLE_MEMORY_INJECTION: the first still emits a small notice so the
    assistant's memory-protocol rule sees a skip signal; the second emits
    nothing.
    """
    result = _run_hook(
        "inject_memory.py", _MINIMAL_PAYLOAD, {"PRAXION_DISABLE_MEMORY_MCP": "1"}
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout != "", "expected disabled notice on stdout"

    payload = json.loads(result.stdout)
    spec = payload["hookSpecificOutput"]
    assert spec["hookEventName"] == "SessionStart"
    context = spec["additionalContext"]
    assert "PRAXION_DISABLE_MEMORY_MCP" in context
    assert "Memory MCP disabled" in context
    # Ensure normal memory content is NOT in the notice output
    assert "Memory Context (auto-injected)" not in context
    assert "Decision Context (auto-injected)" not in context


def test_inject_memory_mcp_flag_always_emits_session_start_event_name():
    """inject_memory.py fires on SessionStart only — hookEventName is always
    SessionStart regardless of whether the payload contains agent_type.

    SubagentStart additionalContext is silently ignored by Claude Code;
    inject_memory.py is no longer registered for SubagentStart events.
    """
    payload = {**_MINIMAL_PAYLOAD, "agent_type": "implementer"}
    result = _run_hook("inject_memory.py", payload, {"PRAXION_DISABLE_MEMORY_MCP": "1"})
    assert result.returncode == 0, result.stderr
    spec = json.loads(result.stdout)["hookSpecificOutput"]
    assert spec["hookEventName"] == "SessionStart"
    assert "PRAXION_DISABLE_MEMORY_MCP" in spec["additionalContext"]


def test_inject_memory_mcp_flag_takes_priority_over_injection_flag():
    """Setting both flags simultaneously should still emit the notice -- the
    MCP flag has priority because it's the unified kill switch and needs
    the observable signal to reach the assistant."""
    result = _run_hook(
        "inject_memory.py",
        _MINIMAL_PAYLOAD,
        {
            "PRAXION_DISABLE_MEMORY_MCP": "1",
            "PRAXION_DISABLE_MEMORY_INJECTION": "1",
        },
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout != "", (
        "MCP flag must win over INJECTION flag so the notice reaches the assistant"
    )
    assert "PRAXION_DISABLE_MEMORY_MCP" in result.stdout
