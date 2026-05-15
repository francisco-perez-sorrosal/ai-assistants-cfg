#!/usr/bin/env python3
"""Notification hook: surface rework session completion as macOS alerts.

Fires on Stop events. Correlates the event back to a rework dispatch via a
marker file written by scripts/dispatch-reworks. Sends a macOS-visible
notification (via osascript) when a Stop event belongs to a rework session,
then deletes the marker.

Async hook (async: true) -- never blocks. Exit 0 unconditionally.

Design notes:
- Marker-file pattern: dispatch-reworks writes ``~/.claude/rework_sessions/<short_id>``
  with the worktree slug as content. The hook reads the Stop payload's
  ``session_id``, derives the short ID (first 8 hex chars before the first
  ``-``), and checks for the marker. If present, the session was dispatched
  by dispatch-reworks; the hook fires and deletes the marker. If absent,
  the Stop event is for an unrelated session — exit silently.
- The Claude Code 2.1.142 Stop payload carries ``session_id`` but NOT
  ``session.name`` and NOT ``reason``. The prior name-prefix + state filter
  silently no-op'd on every Stop event. The marker-file correlation closes
  this gap without requiring payload fields the runtime does not deliver.
- osascript is the only viable notification path for --bg Stop hooks.
  terminalSequence (iTerm2 OSC-9) requires a controlling TTY; detached
  sessions have none.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from _hook_utils import DISABLE_OBSERVABILITY, is_disabled

# Directory where the dispatcher writes per-session marker files.
# Filename = short session ID (8 hex chars); content = worktree slug.
REWORK_MARKERS_DIR = Path.home() / ".claude" / "rework_sessions"

# Claude Code session_ids are UUIDs like "1ab69684-606b-444e-a71f-8cebfeb89290";
# the dispatcher's `claude --bg` output uses the leading 8-hex-char prefix as
# the short ID. Use the same prefix when looking up markers.
SHORT_ID_LENGTH = 8


def _short_id(session_id: str) -> str:
    """Return the 8-char short ID prefix from a full session_id.

    Accepts both bare 8-char IDs and full UUIDs. Returns empty string if
    ``session_id`` is empty or too short.
    """
    if not session_id:
        return ""
    prefix = session_id.split("-", 1)[0]
    return prefix[:SHORT_ID_LENGTH]


def _load_marker(short_id: str) -> str | None:
    """Return the worktree slug from the marker file, or None if no marker exists.

    The marker file content is the worktree slug (single line, no trailing
    newline guaranteed). Whitespace is stripped on read. Missing file or any
    read error returns None — the hook is silent for any session without a
    matching marker.
    """
    if not short_id:
        return None
    marker = REWORK_MARKERS_DIR / short_id
    try:
        return marker.read_text(encoding="utf-8").strip()
    except (OSError, ValueError):
        return None


def _delete_marker(short_id: str) -> None:
    """Best-effort marker deletion after a successful fire.

    Any error (missing file, permission denied) is swallowed — the hook's
    contract is exit 0, and a stale marker is preferable to a hook failure.
    """
    try:
        (REWORK_MARKERS_DIR / short_id).unlink(missing_ok=True)
    except OSError:
        pass


def main() -> None:
    if is_disabled(DISABLE_OBSERVABILITY):
        return

    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    session_id = payload.get("session_id", "")
    short_id = _short_id(session_id)
    slug = _load_marker(short_id)
    if slug is None:
        return

    msg = f"[rework: {slug}] completed"
    subprocess.run(
        [
            "osascript",
            "-e",
            f'display notification "{msg}" with title "Praxion rework"',
        ],
        check=False,
    )
    _delete_marker(short_id)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
