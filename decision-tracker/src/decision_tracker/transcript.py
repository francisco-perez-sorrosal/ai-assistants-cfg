"""Transcript parsing for Claude Code session JSONL files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Noise reduction: assistant text blocks longer than this are truncated.
MAX_TEXT_BLOCK_LENGTH = 2000
TRUNCATED_PREVIEW_LENGTH = 200


def read_transcript(path: Path, since_timestamp: str | None = None) -> str:
    """Read a Claude Code session JSONL file and return extracted conversation text.

    Filters to user and assistant entries, skipping sidechains, meta entries,
    tool results (user entries with list content), and thinking blocks.
    Assistant text blocks exceeding MAX_TEXT_BLOCK_LENGTH are truncated.

    When *since_timestamp* is provided (ISO 8601), only entries at or after
    that timestamp are included (string comparison).
    """
    if not path.is_file():
        return ""

    parts: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            entry = json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            continue

        extracted = _extract_entry(entry, since_timestamp)
        if extracted:
            parts.append(extracted)

    return "\n".join(parts)


def get_last_commit_timestamp(decisions_path: Path, session_id: str) -> str | None:
    """Find the most recent timestamp in decisions.jsonl for *session_id*.

    Returns None when the file does not exist or no entry matches.
    """
    if not decisions_path.is_file():
        return None

    last_timestamp: str | None = None
    for raw_line in decisions_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            entry = json.loads(stripped)
        except (json.JSONDecodeError, ValueError) as exc:
            print(
                f"WARNING: skipping invalid line in {decisions_path}: {exc}",
                file=sys.stderr,
            )
            continue

        if entry.get("session_id") == session_id:
            ts = entry.get("timestamp")
            if ts is not None and (last_timestamp is None or ts > last_timestamp):
                last_timestamp = ts

    return last_timestamp


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_entry(entry: dict, since_timestamp: str | None) -> str | None:
    """Extract displayable text from a single JSONL entry, or None to skip."""
    entry_type = entry.get("type")
    if entry_type not in ("user", "assistant"):
        return None

    if entry.get("isSidechain") is True or entry.get("isMeta") is True:
        return None

    if since_timestamp is not None:
        ts = entry.get("timestamp")
        if ts is None or ts < since_timestamp:
            return None

    if entry_type == "user":
        return _extract_user_content(entry)
    return _extract_assistant_content(entry)


def _extract_user_content(entry: dict) -> str | None:
    """Extract text from a user entry; skip tool_result entries (list content)."""
    content = entry.get("content")
    if not isinstance(content, str):
        return None
    return content


def _extract_assistant_content(entry: dict) -> str | None:
    """Extract text and tool-use placeholders from an assistant entry."""
    content = entry.get("content")
    if not isinstance(content, list):
        return None

    parts: list[str] = []
    for block in content:
        block_type = block.get("type") if isinstance(block, dict) else None
        if block_type == "text":
            text = block.get("text", "")
            if len(text) > MAX_TEXT_BLOCK_LENGTH:
                text = text[:TRUNCATED_PREVIEW_LENGTH] + " [truncated]"
            parts.append(text)
        elif block_type == "tool_use":
            name = block.get("name", "unknown")
            parts.append(f"[tool: {name}]")
        # Skip thinking blocks and anything else

    if not parts:
        return None
    return "\n".join(parts)
