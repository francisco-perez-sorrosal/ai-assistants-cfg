"""JSONL log read/write for decisions.jsonl."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from decision_tracker.schema import Decision


def read_recent(path: Path, count: int = 50) -> list[Decision]:
    """Read the last *count* entries from *path*.

    Returns an empty list when the file does not exist.
    Skips lines that fail JSON parsing or Pydantic validation,
    emitting a warning to stderr for each.
    """
    return _read_validated_lines(path, tail=count)


def read_all(path: Path) -> list[Decision]:
    """Read every valid entry from *path*.

    Same parsing/skip behaviour as :func:`read_recent` but with no count limit.
    """
    return _read_validated_lines(path, tail=None)


def append_decision(path: Path, decision: Decision) -> None:
    """Append *decision* as a single JSON line to *path*.

    Creates the parent directory tree and file if they do not exist.
    Flushes the write to ensure the line is persisted.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(decision.model_dump_json(exclude_none=True) + "\n")
        fh.flush()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _read_validated_lines(path: Path, *, tail: int | None) -> list[Decision]:
    """Parse and validate JSONL lines from *path*.

    When *tail* is not ``None``, only the last *tail* valid entries are returned.
    Invalid lines are skipped with a warning to stderr.
    """
    if not path.is_file():
        return []

    decisions: list[Decision] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        try:
            data = json.loads(stripped)
            decisions.append(Decision.model_validate(data))
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"WARNING: skipping invalid line {line_no} in {path}: {exc}", file=sys.stderr)

    if tail is not None:
        return decisions[-tail:]
    return decisions
