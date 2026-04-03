"""PostToolUse hook: capture tool events as memory observations.

Extracts structured fields using pattern matching (no LLM calls).
Appends a single JSONL line to .ai-state/observations.jsonl.
Async hook (async: true) -- never blocks.
Exit 0 unconditionally.
"""

from __future__ import annotations

import fcntl
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# Tools that generate too much noise to capture
BLOCKLIST = frozenset(
    {
        "Read",
        "Glob",
        "Grep",
        "TodoRead",
        "TodoWrite",
        "TaskList",
        "TaskGet",
        "TaskUpdate",
        "TaskCreate",
    }
)


def classify_event(tool_name: str, file_paths: list[str]) -> str:
    """Classify a tool event based on tool name and file paths."""
    if tool_name in ("Write", "Edit"):
        for fp in file_paths:
            if ".ai-state/decisions/" in fp:
                return "decision"
            if "test_" in fp or "_test." in fp:
                return "test"
            if "src/" in fp:
                return "implementation"
            if fp.endswith(".md"):
                return "documentation"
            config_extensions = (".json", ".toml", ".yaml", ".yml")
            if any(fp.endswith(ext) for ext in config_extensions):
                return "configuration"
    if tool_name == "Bash":
        return "command"
    return "tool_use"


def extract_file_paths(tool_input: dict, tool_name: str) -> list[str]:
    """Extract file paths from tool input."""
    paths: list[str] = []
    if "file_path" in tool_input:
        paths.append(str(tool_input["file_path"]))
    if "path" in tool_input:
        paths.append(str(tool_input["path"]))
    return paths


def _append_observation(obs_path: Path, observation: dict) -> None:
    """Append a single observation to the JSONL file with exclusive locking."""
    obs_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = obs_path.parent / "observations.lock"
    lock_path.touch(exist_ok=True)

    with open(lock_path, "w") as lock_fd:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        try:
            with open(obs_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(observation, separators=(",", ":")) + "\n")
                f.flush()
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    tool_name = payload.get("tool_name", "")
    if tool_name in BLOCKLIST:
        return

    cwd = payload.get("cwd", ".")
    ai_state_dir = Path(cwd) / ".ai-state"
    if not ai_state_dir.exists():
        return  # graceful degradation

    obs_path = ai_state_dir / "observations.jsonl"
    tool_input = payload.get("tool_input", {})
    if isinstance(tool_input, str):
        tool_input = {}

    file_paths = extract_file_paths(tool_input, tool_name)
    classification = classify_event(tool_name, file_paths)

    tool_response = payload.get("tool_response", {})
    has_error = isinstance(tool_response, dict) and tool_response.get("error")
    outcome = "failure" if has_error else "success"

    observation = {
        "timestamp": datetime.now(UTC).isoformat(),
        "session_id": payload.get("session_id", ""),
        "agent_type": payload.get("agent_type", "main"),
        "agent_id": payload.get("agent_id", ""),
        "project": Path(cwd).name,
        "event_type": "tool_use",
        "tool_name": tool_name,
        "file_paths": file_paths,
        "outcome": outcome,
        "classification": classification,
        "metadata": {},
    }

    _append_observation(obs_path, observation)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
