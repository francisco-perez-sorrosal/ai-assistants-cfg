from __future__ import annotations

import json
import os
import subprocess
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MANAGER = REPO_ROOT / "codex" / "config" / "manage-codex-mcp.py"


def make_env(home_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    return env


def run_manager(*args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(MANAGER), *args],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_manage_codex_mcp_install_and_check_round_trip(tmp_path: Path):
    home_dir = tmp_path / "home"
    project_dir = tmp_path / "project"
    home_dir.mkdir()
    project_dir.mkdir()
    env = make_env(home_dir)

    install = run_manager(
        "--repo-root",
        str(REPO_ROOT),
        "--project-root",
        str(project_dir),
        "--mode",
        "install",
        env=env,
    )
    assert install.returncode == 0, install.stderr or install.stdout

    config_path = home_dir / ".codex" / "config.toml"
    parsed = tomllib.loads(config_path.read_text(encoding="utf-8"))
    assert parsed["project_doc_fallback_filenames"] == ["CLAUDE.md"]
    memory_config = parsed["mcp_servers"]["memory"]
    chronograph_config = parsed["mcp_servers"]["task-chronograph"]

    assert memory_config["command"] == "uv"
    assert memory_config["args"] == [
        "run",
        "--project",
        str((REPO_ROOT / "memory-mcp").resolve()),
        "python",
        "-m",
        "memory_mcp",
    ]
    assert memory_config["env"]["MEMORY_FILE"] == ".ai-state/memory.json"
    assert chronograph_config["args"] == [
        "run",
        "--project",
        str((REPO_ROOT / "task-chronograph-mcp").resolve()),
        "python",
        "-m",
        "task_chronograph_mcp",
    ]
    assert chronograph_config["env"]["OTEL_ENABLED"] == "true"

    state_path = home_dir / ".codex" / "praxion" / "mcp_state.json"
    assert state_path.exists()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["installs"] == [
        {
            "project_root": str(project_dir.resolve()),
            "repo_root": str(REPO_ROOT.resolve()),
        }
    ]

    check = run_manager(
        "--repo-root",
        str(REPO_ROOT),
        "--project-root",
        str(project_dir),
        "--mode",
        "check",
        env=env,
    )
    assert check.returncode == 0, check.stderr or check.stdout
    assert check.stdout == ""


def test_manage_codex_mcp_uninstall_restores_user_server_blocks(tmp_path: Path):
    home_dir = tmp_path / "home"
    project_dir = tmp_path / "project"
    home_dir.mkdir()
    project_dir.mkdir()
    env = make_env(home_dir)

    codex_dir = home_dir / ".codex"
    codex_dir.mkdir()
    original_config = (
        '# shared comment\nproject_doc_fallback_filenames = ["TEAM_GUIDE.md"]\n\n'
        '[profiles.default]\nmodel = "gpt-5"\n\n'
        '[mcp_servers.memory]\n# preserve me\ncommand = "python3"\n'
        'args = ["-m", "user_memory"]\nstartup_timeout_sec = 30\n\n'
        '[mcp_servers.memory.env]\nMEMORY_FILE = "user-memory.json"\n'
    )
    (codex_dir / "config.toml").write_text(original_config, encoding="utf-8")

    install = run_manager(
        "--repo-root",
        str(REPO_ROOT),
        "--project-root",
        str(project_dir),
        "--mode",
        "install",
        env=env,
    )
    assert install.returncode == 0, install.stderr or install.stdout

    installed = tomllib.loads((codex_dir / "config.toml").read_text(encoding="utf-8"))
    assert installed["project_doc_fallback_filenames"] == [
        "TEAM_GUIDE.md",
        "CLAUDE.md",
    ]
    assert installed["profiles"]["default"]["model"] == "gpt-5"
    assert installed["mcp_servers"]["memory"]["command"] == "uv"

    uninstall = run_manager(
        "--repo-root",
        str(REPO_ROOT),
        "--project-root",
        str(project_dir),
        "--mode",
        "uninstall",
        env=env,
    )
    assert uninstall.returncode == 0, uninstall.stderr or uninstall.stdout

    restored = (codex_dir / "config.toml").read_text(encoding="utf-8")
    assert restored == original_config
    assert not (codex_dir / "praxion" / "mcp_state.json").exists()


def test_manage_codex_mcp_refcounts_multiple_projects(tmp_path: Path):
    home_dir = tmp_path / "home"
    project_a = tmp_path / "project-a"
    project_b = tmp_path / "project-b"
    home_dir.mkdir()
    project_a.mkdir()
    project_b.mkdir()
    env = make_env(home_dir)

    install_a = run_manager(
        "--repo-root",
        str(REPO_ROOT),
        "--project-root",
        str(project_a),
        "--mode",
        "install",
        env=env,
    )
    assert install_a.returncode == 0, install_a.stderr or install_a.stdout

    install_b = run_manager(
        "--repo-root",
        str(REPO_ROOT),
        "--project-root",
        str(project_b),
        "--mode",
        "install",
        env=env,
    )
    assert install_b.returncode == 0, install_b.stderr or install_b.stdout

    uninstall_a = run_manager(
        "--repo-root",
        str(REPO_ROOT),
        "--project-root",
        str(project_a),
        "--mode",
        "uninstall",
        env=env,
    )
    assert uninstall_a.returncode == 0, uninstall_a.stderr or uninstall_a.stdout

    config_path = home_dir / ".codex" / "config.toml"
    parsed = tomllib.loads(config_path.read_text(encoding="utf-8"))
    assert parsed["project_doc_fallback_filenames"] == ["CLAUDE.md"]
    assert parsed["mcp_servers"]["memory"]["command"] == "uv"

    check_b = run_manager(
        "--repo-root",
        str(REPO_ROOT),
        "--project-root",
        str(project_b),
        "--mode",
        "check",
        env=env,
    )
    assert check_b.returncode == 0, check_b.stderr or check_b.stdout

    uninstall_b = run_manager(
        "--repo-root",
        str(REPO_ROOT),
        "--project-root",
        str(project_b),
        "--mode",
        "uninstall",
        env=env,
    )
    assert uninstall_b.returncode == 0, uninstall_b.stderr or uninstall_b.stdout
    assert not config_path.exists()
    assert not (home_dir / ".codex" / "praxion" / "mcp_state.json").exists()
