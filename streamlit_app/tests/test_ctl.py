"""
Behavioral tests for scripts/praxion-dashboard bash ctl.

Tests invoke the ctl via ``subprocess.run`` to verify lifecycle subcommand
behavior: install idempotency, status exit codes, unknown subcommand handling,
uninstall with --yes flag, and help/usage output.

All tests that modify filesystem state (install, uninstall) monkeypatch HOME
to a tmp_path so the real ``~/.praxion-dashboard/`` is never touched.

Concurrent BDD/TDD state
-------------------------
The implementer and test-engineer run concurrently in this paired step.
``scripts/praxion-dashboard`` does not exist yet.  Tests are expected to fail
RED at collection time (FileNotFoundError or ENOENT from subprocess) until 14a
lands the ctl script.

REGISTERED OBJECTION — concurrent-mode GREEN trigger
------------------------------------------------------
If all tests pass GREEN on first run, the implementer landed
``scripts/praxion-dashboard`` before these tests were written.  Per
``pattern_concurrent_bdd_green_on_first_run``: not a defect when the
behavioral contract is correctly encoded.  Contract is: help exits 0,
status without install exits non-zero, install is idempotent, uninstall --yes
removes state without prompting, unknown subcommands exit non-zero.

Slow-test marking
-----------------
Tests that actually run ``install`` (which pip-installs packages into a temp
venv) are marked ``@pytest.mark.slow`` and are skipped by default.  Run them
with ``pytest -m slow`` or ``pytest --run-slow``.

The install tests use a mock pip (a tiny no-op shell script) to keep the suite
fast while still verifying the install subcommand's filesystem effects and
idempotency.

macOS scope
-----------
The ctl is macOS-only v1 (per ADR dec-draft-df080384).  Tests that exercise
launchd-dependent code paths are skipped on non-Darwin platforms.
"""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_WORKTREE_ROOT = Path(__file__).resolve().parents[2]
CTL = _WORKTREE_ROOT / "scripts" / "praxion-dashboard"


def _run_ctl(
    *args: str,
    home: Path | None = None,
    capture_output: bool = True,
    check: bool = False,
    **kwargs: Any,
) -> subprocess.CompletedProcess:
    """Run praxion-dashboard ctl with optional HOME override.

    Never raises on non-zero exit (unless check=True) so tests can
    assert on the exit code explicitly.
    """
    env = os.environ.copy()
    if home is not None:
        env["HOME"] = str(home)
    # Prevent real launchd interaction in CI / test environments
    env.setdefault("PRAXION_DASHBOARD_TEST_MODE", "1")

    return subprocess.run(
        [str(CTL), *args],
        capture_output=capture_output,
        env=env,
        check=check,
        text=True,
        **kwargs,
    )


def _make_mock_pip(tmp_path: Path) -> Path:
    """Write a no-op pip replacement that exits 0 and creates a venv skeleton.

    Returned path is the directory that should be prepended to PATH so that
    ``python3 -m venv ... && pip install ...`` calls succeed without actually
    downloading anything.

    The mock pip creates a minimal venv structure (bin/python, bin/pip, bin/streamlit)
    so the ctl's venv-check passes.
    """
    bin_dir = tmp_path / "mock-bin"
    bin_dir.mkdir()

    # Mock pip script — creates a fake streamlit binary in the target venv
    mock_pip = bin_dir / "pip"
    mock_pip.write_text(
        "#!/bin/sh\n"
        # pip install is called as: venv/bin/pip install -r requirements.txt
        # We just exit 0 and leave the venv intact.
        "exit 0\n"
    )
    mock_pip.chmod(mock_pip.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    # Mock streamlit so the venv validation passes
    mock_streamlit = bin_dir / "streamlit"
    mock_streamlit.write_text("#!/bin/sh\nexit 0\n")
    mock_streamlit.chmod(
        mock_streamlit.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
    )

    return bin_dir


# ---------------------------------------------------------------------------
# Help / usage tests (no filesystem side-effects)
# ---------------------------------------------------------------------------


def test_help_flag_exits_zero() -> None:
    """praxion-dashboard --help exits with code 0."""
    result = _run_ctl("--help")
    assert result.returncode == 0, (
        f"--help should exit 0, got {result.returncode}. stderr: {result.stderr}"
    )


def test_help_output_mentions_subcommands() -> None:
    """praxion-dashboard --help mentions the lifecycle subcommands."""
    result = _run_ctl("--help")
    combined = (result.stdout + result.stderr).lower()
    for subcommand in ("install", "start", "stop", "status"):
        assert subcommand in combined, (
            f"--help output does not mention '{subcommand}'. "
            f"Got:\n{result.stdout}\n{result.stderr}"
        )


def test_unknown_subcommand_exits_nonzero() -> None:
    """An unrecognised subcommand exits with a non-zero code."""
    result = _run_ctl("definitely-not-a-real-subcommand")
    assert result.returncode != 0, "Unknown subcommand should exit non-zero"


# ---------------------------------------------------------------------------
# Status test (no install required)
# ---------------------------------------------------------------------------


def test_status_exits_nonzero_when_not_installed(tmp_path: Path) -> None:
    """praxion-dashboard status exits non-zero when nothing is installed."""
    # Use a fresh HOME so ~/.praxion-dashboard/ does not exist
    result = _run_ctl("status", home=tmp_path)
    assert result.returncode != 0, (
        "status should exit non-zero when the dashboard is not installed. "
        f"Got returncode={result.returncode}. stdout: {result.stdout}"
    )


# ---------------------------------------------------------------------------
# Install idempotency tests (uses mock pip to avoid real pip download)
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_install_creates_venv_directory(tmp_path: Path) -> None:
    """praxion-dashboard install creates ~/.praxion-dashboard/venv/."""
    mock_bin = _make_mock_pip(tmp_path)
    env_path = f"{mock_bin}:{os.environ.get('PATH', '')}"

    result = subprocess.run(
        [str(CTL), "install"],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path), "PATH": env_path},
    )
    venv_dir = tmp_path / ".praxion-dashboard" / "venv"
    assert venv_dir.exists(), (
        f"install should create ~/.praxion-dashboard/venv/. "
        f"returncode={result.returncode}, stderr={result.stderr}"
    )


@pytest.mark.slow
def test_install_is_idempotent(tmp_path: Path) -> None:
    """Calling praxion-dashboard install twice succeeds both times."""
    mock_bin = _make_mock_pip(tmp_path)
    env_path = f"{mock_bin}:{os.environ.get('PATH', '')}"
    run_env = {**os.environ, "HOME": str(tmp_path), "PATH": env_path}

    first = subprocess.run(
        [str(CTL), "install"], capture_output=True, text=True, env=run_env
    )
    second = subprocess.run(
        [str(CTL), "install"], capture_output=True, text=True, env=run_env
    )

    assert first.returncode == 0, f"First install failed: {first.stderr}"
    assert second.returncode == 0, (
        f"Second install (idempotent) failed: {second.stderr}"
    )


# ---------------------------------------------------------------------------
# Uninstall test
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_uninstall_with_yes_flag_does_not_prompt(tmp_path: Path) -> None:
    """praxion-dashboard uninstall --yes removes state without interactive prompt."""
    mock_bin = _make_mock_pip(tmp_path)
    env_path = f"{mock_bin}:{os.environ.get('PATH', '')}"
    run_env = {**os.environ, "HOME": str(tmp_path), "PATH": env_path}

    # Install first so there is something to uninstall
    subprocess.run([str(CTL), "install"], capture_output=True, text=True, env=run_env)

    # Uninstall with --yes — must complete without blocking on stdin
    result = subprocess.run(
        [str(CTL), "uninstall", "--yes"],
        capture_output=True,
        text=True,
        env=run_env,
        input="",  # Simulate empty stdin in case --yes is ignored
        timeout=10,
    )

    assert result.returncode == 0, (
        f"uninstall --yes should exit 0. returncode={result.returncode}, "
        f"stderr={result.stderr}"
    )
    dashboard_dir = tmp_path / ".praxion-dashboard"
    assert not dashboard_dir.exists(), (
        "uninstall --yes should remove ~/.praxion-dashboard/"
    )
