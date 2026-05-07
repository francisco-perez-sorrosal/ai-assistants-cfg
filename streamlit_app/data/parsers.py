"""Parsers for Praxion artifact files. Pure-Python, no Streamlit imports.

All functions in this module are pure — no caching, no side effects.
Functions accepting a Path raise FileNotFoundError on missing files unless
they are explicitly tolerant (metrics_log, sentinel_log, wip, progress),
which return empty/skeleton results instead.

Frontmatter parsing uses stdlib ``re`` + ``pyyaml`` (dec-draft-1c4350fd):
``pyyaml`` is already a Streamlit transitive dependency; this keeps the
dependency count unchanged and matches the regex-based style of the existing
``scripts/finalize_adrs.py`` and ``scripts/regenerate_adr_index.py``.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

_LOG = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------

# Matches a YAML frontmatter block: exactly `---\n ... \n---\n`
_FRONTMATTER_RE = re.compile(r"^---\n(.+?)\n---\n", re.DOTALL)

# Heading at a specific level: `## Heading Text`
# Built lazily per requested level via _heading_re().
_HEADING_RE_CACHE: dict[int, re.Pattern[str]] = {}

# WIP.md progress checklist line: `- [x] <step-id>: Label text [STATUS]`
# Groups: checkbox, step_id, label, (optional suffix like [COMPLETE]).
_CHECKLIST_LINE_RE = re.compile(
    r"^\s*-\s+\[(?P<check>[xX ])\]\s+"
    r"Step\s+(?P<step_id>\S+?):\s+"
    r"(?P<label>.+?)(?:\s+\[[A-Z_]+\])?\s*$"
)

# PROGRESS.md event line format (from agent-intermediate-documents.md):
#   [TIMESTAMP] [AGENT] Phase N/M: [phase-name] -- summary #label1 #key=value
_EVENT_RE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\]\s+"
    r"\[(?P<agent>[^\]]+)\]\s+"
    r"Phase\s+(?P<phase_id>\S+):\s+"
    r"(?:\[(?P<phase_name>[^\]]+)\]\s+--\s+)?(?P<summary>.+?)$"
)

# Markdown table separator row: `|---|---|...`
_TABLE_SEP_RE = re.compile(r"^\|[\s\-|:]+\|$")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _heading_re(level: int) -> re.Pattern[str]:
    """Return (cached) regex for headings at exactly *level* depth."""
    if level not in _HEADING_RE_CACHE:
        hashes = "#" * level
        _HEADING_RE_CACHE[level] = re.compile(
            rf"^{re.escape(hashes)}\s+(.+?)\s*$", re.MULTILINE
        )
    return _HEADING_RE_CACHE[level]


def _parse_md_table(lines: list[str]) -> pd.DataFrame:
    """Parse a markdown pipe-table from *lines* into a DataFrame.

    The first non-empty line must be the header row.  The separator row
    (``|---|---|...``) is skipped.  Returns an empty DataFrame when there are
    fewer than 2 usable lines (header + at least one data row).
    """
    usable = [ln.strip() for ln in lines if ln.strip()]
    if not usable:
        return pd.DataFrame()

    def _split_row(row: str) -> list[str]:
        parts = row.strip("|").split("|")
        return [p.strip() for p in parts]

    header_row = _split_row(usable[0])

    data_rows: list[list[str]] = []
    for row in usable[1:]:
        if _TABLE_SEP_RE.match(row):
            continue
        data_rows.append(_split_row(row))

    if not data_rows:
        return pd.DataFrame()

    # Trim or pad each data row to match header width.
    width = len(header_row)
    padded = [
        (r[:width] if len(r) >= width else r + [""] * (width - len(r)))
        for r in data_rows
    ]
    return pd.DataFrame(padded, columns=header_row)


def _parse_tail_labels(tail: str) -> tuple[list[str], dict[str, str]]:
    """Extract bare labels and key=value pairs from a PROGRESS event tail.

    *tail* is the space-prefixed sequence of ``#token`` fragments at the end
    of an event line (e.g., ``" #observability #feature=auth"``).
    """
    labels: list[str] = []
    kv: dict[str, str] = {}
    for token in tail.strip().split():
        if not token.startswith("#"):
            continue
        body = token[1:]
        if "=" in body:
            key, _, value = body.partition("=")
            kv[key] = value
        else:
            labels.append(body)
    return labels, kv


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from a markdown file.

    Returns ``(frontmatter_dict, body_text)``.  Returns ``({}, body)`` when no
    frontmatter is present.  The returned body never includes the ``---`` block.

    Raises ``FileNotFoundError`` if *path* does not exist.
    """
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    try:
        metadata: dict[str, Any] = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        metadata = {}
    body = text[match.end() :]
    return metadata, body


def parse_yaml(path: Path) -> Any:
    """Parse a pure YAML file (e.g., ``traceability.yml``).

    Returns the parsed Python structure.

    Raises ``FileNotFoundError`` if *path* is missing.
    Raises ``yaml.YAMLError`` if the file is malformed.
    """
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text)


def parse_md_sections(path: Path, level: int = 2) -> dict[str, str]:
    """Split a markdown file by headings of *level* (``##`` by default).

    Returns ``{heading_text: section_body_excluding_heading_line}``.
    Content before the first matching heading is stored under the empty-string
    key ``""``.  Only headings at exactly *level* depth are matched.

    Raises ``FileNotFoundError`` if *path* does not exist.
    """
    text = path.read_text(encoding="utf-8")
    heading_re = _heading_re(level)

    sections: dict[str, str] = {}
    current_key = ""
    current_lines: list[str] = []

    for line in text.splitlines(keepends=True):
        m = heading_re.match(line)
        if m:
            sections[current_key] = "".join(current_lines)
            current_key = m.group(1)
            current_lines = []
        else:
            current_lines.append(line)

    sections[current_key] = "".join(current_lines)
    return sections


def parse_metrics_log(path: Path) -> pd.DataFrame:
    """Parse ``METRICS_LOG.md`` (append-only Markdown table) into a DataFrame.

    Returns an empty DataFrame when the file is missing or contains no data rows.
    The markdown separator row (``|---|...|``) is skipped automatically.
    """
    if not path.exists():
        return pd.DataFrame()

    lines = path.read_text(encoding="utf-8").splitlines()
    table_lines = [ln for ln in lines if ln.strip().startswith("|")]
    return _parse_md_table(table_lines)


def parse_metrics_report_json(path: Path) -> dict[str, Any]:
    """Parse a ``METRICS_REPORT_*.json`` file.

    Validates that ``schema_version`` is present; if absent, logs a WARNING but
    still returns the parsed dict.

    Raises ``FileNotFoundError`` if *path* is missing.
    Raises ``json.JSONDecodeError`` if the file is malformed JSON.
    """
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if "schema_version" not in data:
        _LOG.warning(
            "METRICS_REPORT JSON at %s is missing 'schema_version' field", path
        )
    return data


def parse_sentinel_log(path: Path) -> pd.DataFrame:
    """Parse ``SENTINEL_LOG.md`` (append-only table) into a DataFrame.

    Columns include timestamp, report_file, health_grade, finding counts, and
    coherence_grade (matching the append-only log schema from
    ``agent-intermediate-documents.md``).

    Returns an empty DataFrame when the file is missing or contains no data rows.
    """
    if not path.exists():
        return pd.DataFrame()

    lines = path.read_text(encoding="utf-8").splitlines()
    table_lines = [ln for ln in lines if ln.strip().startswith("|")]
    return _parse_md_table(table_lines)


_WIP_H2 = re.compile(r"^##\s+(.+?)\s*$")
_WIP_H3 = re.compile(r"^###\s+(.+?)\s*$")
_WIP_PHASE_MARKER = re.compile(r"^\*\*Phase\s+\d+[^*]*\*\*")

_WIP_SECTION_CURRENT = "current_step"
_WIP_SECTION_STATUS = "status"
_WIP_SECTION_PROGRESS = "progress"
_WIP_SECTION_BLOCKERS = "blockers"
_WIP_SECTION_NEXT = "next_action"


def _wip_section_from_heading(heading: str) -> str:
    """Map a lowercase WIP.md heading to a section name constant."""
    if "current step" in heading or "current batch" in heading:
        return _WIP_SECTION_CURRENT
    if "status" in heading:
        return _WIP_SECTION_STATUS
    if "progress" in heading:
        return _WIP_SECTION_PROGRESS
    if "blocker" in heading:
        return _WIP_SECTION_BLOCKERS
    if "next action" in heading:
        return _WIP_SECTION_NEXT
    return ""


def _wip_process_line(
    line: str,
    section: str,
    current_phase: str,
    state: dict[str, Any],
) -> str:
    """Update *state* for one WIP.md line; return the (possibly new) current_phase."""
    stripped = line.strip()

    if section == _WIP_SECTION_CURRENT:
        if stripped and not stripped.startswith("#") and not state["current_step"]:
            state["current_step"] = stripped.lstrip("*").rstrip("*").strip()

    elif section == _WIP_SECTION_STATUS:
        if stripped and not stripped.startswith("#") and not state["status"]:
            state["status"] = stripped.lstrip("[").split("]")[0].strip()

    elif section == _WIP_SECTION_PROGRESS:
        if _WIP_PHASE_MARKER.match(stripped):
            return stripped.strip("*").strip()
        cm = _CHECKLIST_LINE_RE.match(line)
        if cm:
            done = cm.group("check").strip().lower() == "x"
            state["progress"].append(
                {
                    "step_id": cm.group("step_id"),
                    "label": cm.group("label").strip(),
                    "done": done,
                    "phase": current_phase,
                }
            )

    elif section == _WIP_SECTION_BLOCKERS:
        if stripped and not stripped.startswith("#"):
            state["blockers_lines"].append(stripped)

    elif section == _WIP_SECTION_NEXT:
        if stripped and not stripped.startswith("#"):
            state["next_action_lines"].append(stripped)

    return current_phase


def parse_wip(path: Path) -> dict[str, Any]:
    """Parse ``WIP.md`` into structured data.

    Returns a dict with keys:
      - ``current_step`` (str)
      - ``status`` (str)
      - ``progress`` (list of dicts — each with step_id, label, done, phase)
      - ``blockers`` (str)
      - ``next_action`` (str | None)

    Returns a minimal skeleton dict when *path* is missing (tolerant parser).
    """
    if not path.exists():
        return {
            "current_step": "",
            "status": "",
            "progress": [],
            "blockers": "",
            "next_action": None,
        }

    state: dict[str, Any] = {
        "current_step": "",
        "status": "",
        "progress": [],
        "blockers_lines": [],
        "next_action_lines": [],
    }
    section = ""
    current_phase = ""

    for line in path.read_text(encoding="utf-8").splitlines():
        h2 = _WIP_H2.match(line)
        if h2:
            section = _wip_section_from_heading(h2.group(1).lower())
            continue
        h3 = _WIP_H3.match(line)
        if h3 and section == _WIP_SECTION_PROGRESS:
            current_phase = h3.group(1)
            continue
        current_phase = _wip_process_line(line, section, current_phase, state)

    return {
        "current_step": state["current_step"],
        "status": state["status"],
        "progress": state["progress"],
        "blockers": "\n".join(state["blockers_lines"]).strip(),
        "next_action": "\n".join(state["next_action_lines"]).strip() or None,
    }


_PROGRESS_PHASE_RE = re.compile(
    r"Phase\s+(?P<phase_id>\S+):\s+"
    r"(?:\[(?P<phase_name>[^\]]+)\]\s+--\s+)?(?P<summary>.+?)$"
)


def _parse_progress_brackets(line: str) -> tuple[str, str, str] | None:
    """Extract (timestamp, agent, rest) from a PROGRESS event line.

    Returns ``None`` if the line is malformed.
    """
    if not line.startswith("["):
        return None
    try:
        ts_end = line.index("]")
        timestamp = line[1:ts_end]
        rest = line[ts_end + 1 :].lstrip()
        if not rest.startswith("["):
            return None
        agent_end = rest.index("]")
        agent = rest[1:agent_end]
        rest = rest[agent_end + 1 :].lstrip()
        return timestamp, agent, rest
    except ValueError:
        return None


def _parse_progress_phase(main_part: str) -> tuple[str, str]:
    """Parse ``Phase N/M: [name] -- summary`` into ``(phase, summary)``."""
    m = _PROGRESS_PHASE_RE.match(main_part)
    if not m:
        return "", main_part
    phase_name = m.group("phase_name") or ""
    phase_id = m.group("phase_id")
    summary_text = m.group("summary").strip()
    phase = f"{phase_id}: {phase_name}".rstrip(": ") if phase_name else phase_id
    return phase, summary_text


def _parse_progress_line(line: str) -> dict[str, Any] | None:
    """Parse one PROGRESS.md event line into an event dict, or ``None`` if malformed."""
    parsed = _parse_progress_brackets(line)
    if parsed is None:
        return None
    timestamp, agent, rest = parsed
    if not rest.startswith("Phase "):
        return None
    hash_pos = rest.find(" #")
    main_part = rest if hash_pos == -1 else rest[:hash_pos]
    tail = "" if hash_pos == -1 else rest[hash_pos:]
    labels, kv = _parse_tail_labels(tail)
    phase, summary_text = _parse_progress_phase(main_part)
    return {
        "timestamp": timestamp,
        "agent": agent,
        "phase": phase,
        "summary": summary_text,
        "labels": labels,
        "kv": kv,
    }


def parse_progress(path: Path) -> list[dict[str, Any]]:
    """Parse ``PROGRESS.md`` into a list of phase-transition event dicts.

    Each event: ``{timestamp, agent, phase, summary, labels, kv}``.
    Format: ``[TIMESTAMP] [AGENT] Phase N/M: [name] -- summary #label #k=v``
    Returns ``[]`` on missing file; malformed lines are silently skipped.
    """
    if not path.exists():
        return []
    events = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        event = _parse_progress_line(raw_line.strip())
        if event is not None:
            events.append(event)
    return events
