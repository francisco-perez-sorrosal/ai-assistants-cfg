"""Tests for scripts/check_id_citation_discipline.py.

Regression coverage for the extensionless-bash gap discovered during the
Phase 2 dispatch-reworks pipeline verifier pass: bash scripts without a `.sh`
extension (e.g., `scripts/dispatch-reworks`) were previously skipped by the
detector because file selection was extension-only. The shebang-detection
extension closes that gap.
"""

from __future__ import annotations

import stat
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHECKER = PROJECT_ROOT / "scripts" / "check_id_citation_discipline.py"


def _make_exec_script(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )


def test_explicit_extensionless_bash_with_violation_is_detected(tmp_path: Path) -> None:
    script = tmp_path / "scripts" / "my-tool"
    _make_exec_script(
        script, "#!/usr/bin/env bash\n# Step 1 smoke-check should be caught\necho hi\n"
    )

    result = _run(
        ["--files", str(script), "--repo-root", str(tmp_path)],
        cwd=tmp_path,
    )

    assert result.returncode == 1, (
        f"expected exit 1; got {result.returncode}\n{result.stdout}\n{result.stderr}"
    )
    assert "step-ref" in result.stdout
    assert "Step 1" in result.stdout


def test_explicit_extensionless_bash_clean_returns_zero(tmp_path: Path) -> None:
    script = tmp_path / "scripts" / "clean-tool"
    _make_exec_script(script, "#!/usr/bin/env bash\necho hello world\n")

    result = _run(
        ["--files", str(script), "--repo-root", str(tmp_path)],
        cwd=tmp_path,
    )

    assert result.returncode == 0, (
        f"expected exit 0; got {result.returncode}\n{result.stdout}"
    )


def test_full_scan_finds_extensionless_executable_bash(tmp_path: Path) -> None:
    script = tmp_path / "scripts" / "another-tool"
    _make_exec_script(script, "#!/bin/bash\n# REQ-FOO-01 should be caught\n")

    result = _run(["--repo-root", str(tmp_path)], cwd=tmp_path)

    assert result.returncode == 1
    assert "REQ-FOO-01" in result.stdout or "req-id" in result.stdout


def test_full_scan_skips_extensionless_non_bash(tmp_path: Path) -> None:
    """Extensionless text files without a bash shebang are not scanned."""
    readme = tmp_path / "README"
    readme.write_text("# Step 1 — historical chapter heading, not a citation\n")
    readme.chmod(readme.stat().st_mode | stat.S_IXUSR)

    result = _run(["--repo-root", str(tmp_path)], cwd=tmp_path)

    assert result.returncode == 0


def test_full_scan_skips_extensionless_bash_without_exec_bit(tmp_path: Path) -> None:
    """In full-repo mode the executable-bit heuristic skips non-exec bash files."""
    not_exec = tmp_path / "scripts" / "not-executable"
    not_exec.parent.mkdir(parents=True)
    not_exec.write_text(
        "#!/usr/bin/env bash\n# Step 9 — should NOT trigger in full scan\n"
    )
    # Intentionally do not chmod +x.

    result = _run(["--repo-root", str(tmp_path)], cwd=tmp_path)

    assert result.returncode == 0


def test_explicit_pass_bypasses_exec_bit_heuristic(tmp_path: Path) -> None:
    """Explicit --files passes scan extensionless bash regardless of exec bit."""
    script = tmp_path / "scripts" / "sourceable-lib"
    script.parent.mkdir(parents=True)
    script.write_text("#!/usr/bin/env bash\n# Step 4 leak in a sourceable bash lib\n")
    # No exec bit on purpose.

    result = _run(
        ["--files", str(script), "--repo-root", str(tmp_path)],
        cwd=tmp_path,
    )

    assert result.returncode == 1
    assert "Step 4" in result.stdout


def test_shebang_other_shells_recognized(tmp_path: Path) -> None:
    for shell_path in ("/bin/sh", "/usr/bin/env zsh", "/bin/dash", "/usr/bin/env ksh"):
        script = (
            tmp_path / f"scripts/tool-{shell_path.replace('/', '_').replace(' ', '_')}"
        )
        _make_exec_script(script, f"#!{shell_path}\n# REQ-X-01\n")
        result = _run(
            ["--files", str(script), "--repo-root", str(tmp_path)],
            cwd=tmp_path,
        )
        assert result.returncode == 1, f"shebang {shell_path!r} not recognized"
