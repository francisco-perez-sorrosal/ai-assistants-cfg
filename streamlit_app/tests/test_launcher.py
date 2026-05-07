"""
Behavioral tests for streamlit_app/launcher.py.

The launcher module is a pure subprocess wrapper — no Streamlit imports.
It derives per-project ports, manages the venv path, and spawns the
Streamlit subprocess with the correct environment.

Concurrent BDD/TDD state
------------------------
The implementer and test-engineer run concurrently in this paired step.
The current ``launcher.py`` raises ``NotImplementedError`` entirely.
Every test here is expected to fail (RED) until 14a lands.

REGISTERED OBJECTION — concurrent-mode GREEN trigger
------------------------------------------------------
If all tests pass GREEN on first run, the implementer already landed
launcher.py before these tests were written. Per
``pattern_concurrent_bdd_green_on_first_run``: register objection and
verify the behavioral contract (not just that code exists). Behavioral
contract encoded here covers port derivation invariants, venv path
resolution, and subprocess environment forwarding.

Port derivation contract (from ADR dec-draft-dd356bb0)
-------------------------------------------------------
  port = 8501 + int.from_bytes(sha256(abs_path.encode()).digest()[:2], 'big') % 1000
Range: 8501–9500. Deterministic per project absolute path. Mirrors the
chronograph-ctl pattern (sha256(abs_path) % range).

Deferred imports
----------------
All production imports happen inside test bodies to keep pytest
collection independent of the launcher stub state.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Port derivation tests
# ---------------------------------------------------------------------------


def test_derive_port_is_deterministic_for_same_root(tmp_path: Path) -> None:
    """Same project root always produces the same port."""
    from streamlit_app.launcher import derive_port  # noqa: PLC0415

    root = tmp_path / "my-project"
    root.mkdir()
    assert derive_port(root) == derive_port(root)


def test_derive_port_is_different_for_different_roots(tmp_path: Path) -> None:
    """Different absolute project paths produce different ports (with high probability)."""
    from streamlit_app.launcher import derive_port  # noqa: PLC0415

    roots = [tmp_path / f"project-{i}" for i in range(4)]
    for r in roots:
        r.mkdir()

    ports = [derive_port(r) for r in roots]
    # All four absolute paths are distinct → expect all ports distinct.
    # (Birthday collision at 4 paths in a 1000-slot range is negligible.)
    assert len(set(ports)) == len(ports), (
        f"Expected all ports distinct, got {ports} for roots {[str(r) for r in roots]}"
    )


def test_derive_port_in_valid_range(tmp_path: Path) -> None:
    """Derived port falls in the documented 8501–9500 range."""
    from streamlit_app.launcher import derive_port  # noqa: PLC0415

    root = tmp_path / "rangecheck"
    root.mkdir()
    port = derive_port(root)
    assert 8501 <= port <= 9500, f"Port {port} is outside the 8501–9500 range"


def test_derive_port_matches_sha256_formula(tmp_path: Path) -> None:
    """Port derivation exactly matches the documented sha256 formula from ADR."""
    from streamlit_app.launcher import derive_port  # noqa: PLC0415

    root = tmp_path / "formula-check"
    root.mkdir()
    abs_path = str(root.resolve())
    digest = hashlib.sha256(abs_path.encode()).digest()
    expected = 8501 + int.from_bytes(digest[:2], "big") % 1000

    assert derive_port(root) == expected


# ---------------------------------------------------------------------------
# find_venv tests
# ---------------------------------------------------------------------------
# GOTCHA: VENV_HOME is a module-level constant computed at import time via
# Path.home(). monkeypatch.setenv("HOME", ...) cannot affect it after import.
# Patch the module attribute directly to control the venv path in tests.
# ---------------------------------------------------------------------------


def test_find_venv_raises_when_venv_absent(tmp_path: Path) -> None:
    """find_venv() raises FileNotFoundError when the configured venv path is absent."""
    import streamlit_app.launcher as launcher_mod  # noqa: PLC0415
    from streamlit_app.launcher import find_venv  # noqa: PLC0415

    absent_venv = tmp_path / ".praxion-dashboard" / "venv"
    # absent_venv does NOT exist — should raise

    with patch.object(launcher_mod, "VENV_HOME", absent_venv):
        with pytest.raises(FileNotFoundError):
            find_venv()


def test_find_venv_returns_path_when_venv_exists(tmp_path: Path) -> None:
    """find_venv() returns the venv Path when the configured venv directory exists."""
    import streamlit_app.launcher as launcher_mod  # noqa: PLC0415
    from streamlit_app.launcher import find_venv  # noqa: PLC0415

    venv_dir = tmp_path / ".praxion-dashboard" / "venv"
    venv_dir.mkdir(parents=True)

    with patch.object(launcher_mod, "VENV_HOME", venv_dir):
        result = find_venv()

    assert result == venv_dir


# ---------------------------------------------------------------------------
# launch() subprocess environment test
# ---------------------------------------------------------------------------
# launch() calls find_venv() then checks for bin/streamlit in the venv.
# We patch VENV_HOME to a tmp directory and create a fake streamlit binary
# so the path-existence checks pass before subprocess.Popen is intercepted.
# ---------------------------------------------------------------------------


def _make_fake_venv(tmp_path: Path) -> Path:
    """Create a minimal fake venv with a placeholder streamlit binary."""
    venv = tmp_path / ".praxion-dashboard" / "venv"
    streamlit_bin = venv / "bin" / "streamlit"
    streamlit_bin.parent.mkdir(parents=True)
    streamlit_bin.write_text("#!/bin/sh\nexit 0\n")
    import stat  # noqa: PLC0415

    streamlit_bin.chmod(
        streamlit_bin.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
    )
    return venv


def test_launch_passes_project_root_in_subprocess_env(tmp_path: Path) -> None:
    """launch() forwards PRAXION_PROJECT_ROOT to the streamlit subprocess environment."""
    import streamlit_app.launcher as launcher_mod  # noqa: PLC0415
    from streamlit_app.launcher import launch  # noqa: PLC0415

    project_root = tmp_path / "my-project"
    project_root.mkdir()
    fake_venv = _make_fake_venv(tmp_path)

    captured_kwargs: dict = {}

    def fake_popen(*args: object, **kwargs: object) -> MagicMock:
        captured_kwargs.update(kwargs)
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        return mock_proc

    with patch.object(launcher_mod, "VENV_HOME", fake_venv):
        with patch("subprocess.Popen", side_effect=fake_popen):
            launch(project_root)

    env = captured_kwargs.get("env", {})
    assert "PRAXION_PROJECT_ROOT" in env, (
        "PRAXION_PROJECT_ROOT must be forwarded to the Streamlit subprocess environment"
    )
    assert env["PRAXION_PROJECT_ROOT"] == str(project_root.resolve())


def test_launch_uses_derived_port_when_no_port_given(tmp_path: Path) -> None:
    """launch() uses derive_port() when no explicit port is provided."""
    import streamlit_app.launcher as launcher_mod  # noqa: PLC0415
    from streamlit_app.launcher import derive_port, launch  # noqa: PLC0415

    project_root = tmp_path / "auto-port"
    project_root.mkdir()
    fake_venv = _make_fake_venv(tmp_path)
    expected_port = derive_port(project_root)

    captured_args: list = []

    def fake_popen(*args: object, **kwargs: object) -> MagicMock:
        if args:
            captured_args.extend(args[0] if isinstance(args[0], list) else [args[0]])
        mock_proc = MagicMock()
        mock_proc.pid = 99
        return mock_proc

    with patch.object(launcher_mod, "VENV_HOME", fake_venv):
        with patch("subprocess.Popen", side_effect=fake_popen):
            returned_port = launch(project_root)

    assert returned_port == expected_port
    # The derived port must appear somewhere in the subprocess command
    assert any(str(expected_port) in str(a) for a in captured_args), (
        f"Expected port {expected_port} in subprocess args, got {captured_args}"
    )


def test_launch_uses_explicit_port_when_provided(tmp_path: Path) -> None:
    """launch() uses the caller-supplied port instead of deriving one."""
    import streamlit_app.launcher as launcher_mod  # noqa: PLC0415
    from streamlit_app.launcher import launch  # noqa: PLC0415

    project_root = tmp_path / "explicit-port"
    project_root.mkdir()
    fake_venv = _make_fake_venv(tmp_path)
    explicit_port = 8765

    captured_args: list = []

    def fake_popen(*args: object, **kwargs: object) -> MagicMock:
        if args:
            captured_args.extend(args[0] if isinstance(args[0], list) else [args[0]])
        mock_proc = MagicMock()
        mock_proc.pid = 42
        return mock_proc

    with patch.object(launcher_mod, "VENV_HOME", fake_venv):
        with patch("subprocess.Popen", side_effect=fake_popen):
            returned_port = launch(project_root, port=explicit_port)

    assert returned_port == explicit_port
    assert any(str(explicit_port) in str(a) for a in captured_args), (
        f"Expected port {explicit_port} in subprocess args, got {captured_args}"
    )
