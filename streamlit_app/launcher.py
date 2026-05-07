"""Launcher for the Praxion Pipeline Dashboard.

Resolves project root, derives a deterministic per-project port, and launches
streamlit run app.py inside the dedicated venv.

This module intentionally does NOT import Streamlit.  It is a pure subprocess
wrapper and can run in any Python 3.11+ environment.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────────────────

VENV_HOME = Path.home() / ".praxion-dashboard" / "venv"
PORT_BASE = 8501
PORT_SPAN = 1000  # range 8501–9500


# ── Port derivation ────────────────────────────────────────────────────────────


def derive_port(project_root: Path) -> int:
    """Compute deterministic per-project port using sha256(abs_path).

    Formula: ``PORT_BASE + sha256(abs_path)[:2-bytes-as-int] % PORT_SPAN``
    Range: 8501–9500.  Mirrors the chronograph-ctl derivation pattern.

    Two projects with different absolute paths produce different ports
    (within the collision probability of sha256 truncated to 2 bytes
    across 1000 slots).
    """
    abs_path = str(project_root.resolve()).encode("utf-8")
    digest = hashlib.sha256(abs_path).digest()
    offset = int.from_bytes(digest[:2], "big") % PORT_SPAN
    return PORT_BASE + offset


# ── Venv resolution ────────────────────────────────────────────────────────────


def find_venv() -> Path:
    """Return the dedicated venv path.

    Raises
    ------
    FileNotFoundError
        When the venv has not been installed yet.
    """
    if not VENV_HOME.exists():
        raise FileNotFoundError(
            f"Praxion dashboard venv not found at {VENV_HOME}. "
            "Run `praxion-dashboard install` first."
        )
    return VENV_HOME


# ── Launcher ───────────────────────────────────────────────────────────────────


def launch(project_root: Path, port: int | None = None) -> int:
    """Launch the Streamlit subprocess (foreground; ctl handles backgrounding).

    Sets ``PRAXION_PROJECT_ROOT`` in the subprocess environment and runs with
    ``cwd`` equal to the resolved project root so relative imports inside
    pages work correctly.

    Parameters
    ----------
    project_root:
        Absolute path to the target Praxion project.
    port:
        Port override.  When ``None`` the sha256-derived port is used.

    Returns
    -------
    int
        The bound port number.
    """
    resolved_root = project_root.resolve()
    if port is None:
        port = derive_port(resolved_root)

    venv = find_venv()
    streamlit_bin = venv / "bin" / "streamlit"
    if not streamlit_bin.exists():
        raise FileNotFoundError(
            f"streamlit not found in venv at {streamlit_bin}. "
            "Re-run `praxion-dashboard install` to repair the venv."
        )

    app_py = Path(__file__).parent / "app.py"

    env = {**os.environ, "PRAXION_PROJECT_ROOT": str(resolved_root)}

    cmd = [
        str(streamlit_bin),
        "run",
        str(app_py),
        "--server.port",
        str(port),
        "--server.address",
        "127.0.0.1",
        "--browser.gatherUsageStats",
        "false",
    ]

    subprocess.Popen(cmd, cwd=str(resolved_root), env=env)
    return port


# ── CLI entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else os.getcwd()).resolve()
    bound = launch(root)
    print(f"Streamlit started on port {bound} for project {root}")
