"""Timeline and session narrative formatters for observation data.

Pure functions that transform observation dicts into readable Markdown.
Used by the ``timeline`` and ``session_narrative`` MCP tools.
"""

from __future__ import annotations

from collections import defaultdict

# -- Constants ----------------------------------------------------------------

NO_OBSERVATIONS_MESSAGE = "No observations found."

# Classification labels used in narrative grouping
CLASSIFICATION_DECISION = "decision"


# -- Timeline -----------------------------------------------------------------


def build_timeline(observations: list[dict], query_description: str = "") -> str:
    """Format observations as a compact chronological Markdown timeline.

    Groups entries by date (``## YYYY-MM-DD``) and formats each as::

        HH:MM [agent_type] tool_name -> outcome (file1, file2)

    Lifecycle events (session_start, session_stop, etc.) render without
    a tool name.

    Returns *NO_OBSERVATIONS_MESSAGE* when the list is empty.
    """
    if not observations:
        return NO_OBSERVATIONS_MESSAGE

    grouped = _group_by_date(observations)
    lines: list[str] = []

    if query_description:
        lines.append(f"# Timeline: {query_description}")
        lines.append("")

    for date_key in sorted(grouped.keys()):
        lines.append(f"## {date_key}")
        for obs in grouped[date_key]:
            lines.append(_format_timeline_line(obs))
        lines.append("")

    return "\n".join(lines).rstrip()


# -- Session narrative --------------------------------------------------------


def build_session_narrative(observations: list[dict]) -> str:
    """Build a structured Markdown narrative from session observations.

    Sections:

    - **What Was Done** -- tool uses grouped by classification
    - **Files Touched** -- deduplicated file paths (written vs read)
    - **Decisions Made** -- observations with ``classification == "decision"``
    - **Outcome** -- success/failure counts
    """
    if not observations:
        return NO_OBSERVATIONS_MESSAGE

    lines: list[str] = []
    lines.append("# Session Narrative")
    lines.append("")

    _append_what_was_done(lines, observations)
    _append_files_touched(lines, observations)
    _append_decisions_made(lines, observations)
    _append_outcome(lines, observations)

    return "\n".join(lines).rstrip()


# -- Internal helpers ---------------------------------------------------------


def _group_by_date(observations: list[dict]) -> dict[str, list[dict]]:
    """Group observations by the date portion of their timestamp."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    for obs in observations:
        ts = obs.get("timestamp", "")
        date_key = ts[:10] if len(ts) >= 10 else "unknown"
        grouped[date_key].append(obs)
    return grouped


def _format_timeline_line(obs: dict) -> str:
    """Format a single observation as a compact timeline line."""
    ts = obs.get("timestamp", "")
    time_part = ts[11:16] if len(ts) >= 16 else "??:??"

    agent = obs.get("agent_type", "unknown")
    tool = obs.get("tool_name")
    event_type = obs.get("event_type", "")
    outcome = obs.get("outcome", "")
    file_paths = obs.get("file_paths", [])

    summary = obs.get("summary", "")

    # Build the action portion
    if summary:
        action = summary
    elif tool:
        action = tool
    elif event_type:
        action = event_type
    else:
        action = "unknown"

    # Build the suffix (only when no summary — summary already contains the details)
    parts: list[str] = []
    if not summary:
        if outcome:
            parts.append(f"-> {outcome}")
        if file_paths:
            files_str = ", ".join(file_paths[:3])
            if len(file_paths) > 3:
                files_str += f" +{len(file_paths) - 3} more"
            parts.append(f"({files_str})")

    suffix = " ".join(parts)
    line = f"{time_part} [{agent}] {action}"
    if suffix:
        line = f"{line} {suffix}"
    return line


def _append_what_was_done(lines: list[str], observations: list[dict]) -> None:
    """Append 'What Was Done' section grouped by classification."""
    lines.append("## What Was Done")
    lines.append("")

    by_classification: dict[str, list[str]] = defaultdict(list)
    for obs in observations:
        classification = obs.get("classification") or obs.get("event_type") or "other"
        summary = obs.get("summary", "")
        by_classification[classification].append(summary)

    for classification in sorted(by_classification.keys()):
        summaries = by_classification[classification]
        count = len(summaries)
        lines.append(f"- **{classification}** ({count}):")
        # Show up to 5 summaries per classification
        for s in summaries[:5]:
            if s:
                lines.append(f"  - {s}")
        if count > 5:
            lines.append(f"  - ... and {count - 5} more")

    lines.append("")


def _append_files_touched(lines: list[str], observations: list[dict]) -> None:
    """Append 'Files Touched' section with deduplicated file paths."""
    lines.append("## Files Touched")
    lines.append("")

    all_files: set[str] = set()
    for obs in observations:
        for fp in obs.get("file_paths", []):
            all_files.add(fp)

    if not all_files:
        lines.append("No file paths recorded.")
    else:
        for fp in sorted(all_files):
            lines.append(f"- `{fp}`")

    lines.append("")


def _append_decisions_made(lines: list[str], observations: list[dict]) -> None:
    """Append 'Decisions Made' section from decision-classified observations."""
    lines.append("## Decisions Made")
    lines.append("")

    decisions = [
        obs for obs in observations if obs.get("classification") == CLASSIFICATION_DECISION
    ]

    if not decisions:
        lines.append("No decisions recorded.")
    else:
        for obs in decisions:
            summary = obs.get("summary", "")
            file_paths = obs.get("file_paths", [])
            ts = obs.get("timestamp", "")
            time_part = ts[11:16] if len(ts) >= 16 else ""
            desc = summary or ", ".join(file_paths) or obs.get("tool_name", "unknown")
            prefix = f"{time_part} " if time_part else ""
            lines.append(f"- {prefix}{desc}")

    lines.append("")


def _append_outcome(lines: list[str], observations: list[dict]) -> None:
    """Append 'Outcome' section with success/failure counts."""
    lines.append("## Outcome")
    lines.append("")

    successes = sum(1 for obs in observations if obs.get("outcome") == "success")
    failures = sum(1 for obs in observations if obs.get("outcome") == "failure")
    total = len(observations)
    other = total - successes - failures

    parts: list[str] = [f"{total} total events"]
    if successes:
        parts.append(f"{successes} succeeded")
    if failures:
        parts.append(f"{failures} failed")
    if other:
        parts.append(f"{other} without outcome")

    lines.append(", ".join(parts) + ".")
