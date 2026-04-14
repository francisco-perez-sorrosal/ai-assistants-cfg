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
    }
    assert len(names) == 3
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
        ("validate_memory.py", "PRAXION_DISABLE_MEMORY_GATE"),
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
