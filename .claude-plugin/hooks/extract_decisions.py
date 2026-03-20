#!/usr/bin/env python3
"""Decision extraction hook -- intercepts git commit to extract decisions.

Delegates to the decision-tracker package for extraction and logging.
Follows the fail-open principle: never blocks commits due to internal errors.
"""

import json
import os
import re
import subprocess
import sys

GIT_COMMIT_RE = re.compile(r"git\s+commit")
SUBPROCESS_TIMEOUT_SECONDS = 25  # 5s buffer within the 30s hook timeout


def main():
    # Consume ALL stdin to avoid broken pipe (matching existing hook pattern)
    raw = sys.stdin.read()

    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return

    # Only process git commit commands
    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "")
    if not GIT_COMMIT_RE.search(command):
        return

    # Delegate to decision-tracker package
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    project_path = os.path.join(plugin_root, "decision-tracker")

    result = subprocess.run(
        [
            "uv", "run", "--project", project_path,
            "python", "-m", "decision_tracker", "extract",
        ],
        input=raw,
        capture_output=True,
        text=True,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )

    # Forward stderr (hook output goes to stderr for Claude Code to read)
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")

    sys.exit(result.returncode)


if __name__ == "__main__":
    try:
        main()
    except subprocess.TimeoutExpired:
        print("decision-tracker: extraction timed out", file=sys.stderr)
    except FileNotFoundError:
        # uv not found -- degrade silently
        print("decision-tracker: uv not found, skipping extraction", file=sys.stderr)
    except Exception:
        pass
