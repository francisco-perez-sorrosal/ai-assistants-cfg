"""Run ``sentrux check .`` and write a per-run report triple under ``.ai-state/metrics_reports/``.

Each invocation writes three artifacts, mirroring the ``/project-metrics``
artifact triple shape (per-run JSON + per-run MD + append-only log row)
so both signal sources live in the same canonical metrics_reports/
directory and can share consumers (the static HTML viewer at
``.ai-state/metrics_reports/index.html``, future tooling).

Artifacts written per run:

    .ai-state/metrics_reports/SENTRUX_REPORT_<YYYY-MM-DD_HH-MM-SS>.json
    .ai-state/metrics_reports/SENTRUX_REPORT_<YYYY-MM-DD_HH-MM-SS>.md
    .ai-state/metrics_reports/SENTRUX_HISTORY.md   # one row appended

Why a side-car triple instead of folding sentrux into the canonical
aggregate: the ``/project-metrics`` aggregate column tuple is frozen by
ADR (the test suite asserts it verbatim), and sentrux is still advisory
per ``skills/sentrux/SKILL.md`` § 7. The side-car shape keeps both surfaces
visible without crystallizing sentrux into a frozen column prematurely.

Log row schema (column order is load-bearing — the HTML viewer reads by
position):

    | timestamp | commit_sha | quality_signal | rules_checked
    | rules_pass | files_kept | import_edges | call_edges
    | inherit_edges | exit_code |

Every cell that cannot be parsed becomes the literal ``—`` so the JS
``parseValue`` helper renders it as a gap in the chart instead of a
spurious zero. ``rules_pass`` is the boolean ``true`` / ``false`` (string)
mirror of the ``sentrux check`` exit code.

Invocation:

    python3 scripts/sentrux_history.py append [--repo-root .] [--sentrux-bin sentrux]

Idempotent at the file-creation level only — every invocation writes a
fresh report pair (timestamped) and appends one log row. Pruning is a
deliberate user action; see ``Mid-history pruning policy`` in
``docs/metrics/README.md`` for the analogous policy on the canonical
metrics log.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_HISTORY_FILENAME = "SENTRUX_HISTORY.md"
_REPORT_FILENAME_PREFIX = "SENTRUX_REPORT_"
_METRICS_REPORTS_DIRNAME = Path(".ai-state") / "metrics_reports"
_NULL_CELL = "—"
# Numeric fields parsed from sentrux output — kept in one tuple so the
# null-fallback dict and the per-run JSON conversion can both iterate it.
_NUMERIC_FIELDS: tuple[str, ...] = (
    "quality_signal",
    "rules_checked",
    "files_kept",
    "import_edges",
    "call_edges",
    "inherit_edges",
)

_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "commit_sha",
    "quality_signal",
    "rules_checked",
    "rules_pass",
    "files_kept",
    "import_edges",
    "call_edges",
    "inherit_edges",
    "exit_code",
)


def _header_block() -> str:
    """Return the two-line markdown header (header row + separator).

    The shape matches ``aggregate_header_for_log()`` in
    ``scripts/project_metrics/schema.py`` so the JS log-parser at
    ``.ai-state/metrics_reports/index.html`` can split rows with one helper.
    """
    header = "| " + " | ".join(_COLUMNS) + " |"
    separator = "| " + " | ".join(["---"] * len(_COLUMNS)) + " |"
    return header + "\n" + separator + "\n"


def _utc_now_iso() -> str:
    """Return the current UTC instant as an ISO 8601 string with trailing ``Z``."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _filename_timestamp() -> str:
    """Return the filename-safe UTC timestamp ``YYYY-MM-DD_HH-MM-SS``.

    Matches ``METRICS_REPORT_<timestamp>.{md,json}`` exactly so the two
    artifact families sort interleaved-by-time when listed alphabetically.
    No colons — portable across macOS, Linux, Windows.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")


def _to_json_number(cell: str) -> int | None:
    """Convert a parsed cell to ``int`` for JSON; ``_NULL_CELL`` becomes ``None``.

    The text-parse layer keeps everything as strings so the markdown row
    can render ``—`` for unparseable fields. JSON consumers want
    ``null`` and ``int``; this helper makes the conversion in one place.
    """
    if cell == _NULL_CELL:
        return None
    try:
        return int(cell)
    except ValueError:
        return None


def _git_commit_sha(repo_root: Path) -> str:
    """Return the short HEAD SHA, or ``—`` when git or HEAD is unavailable."""
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
    except (
        FileNotFoundError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ):
        return _NULL_CELL
    return completed.stdout.strip() or _NULL_CELL


def _run_sentrux_check(sentrux_bin: str, repo_root: Path) -> tuple[str, int]:
    """Run ``sentrux check <repo_root>``; return (combined_output, exit_code).

    Uses a 60-second budget — sentrux walks the full source tree and
    builds the call graph, so the budget mirrors the ``scc`` collector's
    collect timeout. Returns ``("", 127)`` when the binary is missing so
    the caller emits a sensible row rather than crashing.
    """
    if shutil.which(sentrux_bin) is None:
        return ("", 127)
    try:
        completed = subprocess.run(
            [sentrux_bin, "check", str(repo_root)],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ("", 124)
    combined = (completed.stdout or "") + (completed.stderr or "")
    return (combined, completed.returncode)


def _parse_int_after(pattern: str, text: str) -> str:
    """Return the first ``int`` group matched by ``pattern`` in ``text``, else ``—``.

    The pattern must contain exactly one capture group. Centralizing the
    regex apply lets every parse field share the same null sentinel.
    """
    match = re.search(pattern, text)
    if match is None:
        return _NULL_CELL
    return match.group(1)


def _parse_sentrux_output(output: str) -> dict[str, str]:
    """Extract the columns we display from ``sentrux check`` text output.

    Brittle by necessity — ``sentrux check`` has no ``--json`` flag in
    v0.5.7. Each field is parsed independently; an unparseable field
    becomes ``_NULL_CELL`` rather than raising. The patterns target the
    stable substrings (the bracketed log prefixes are stable across
    recent versions; the trailing ``Quality:`` and ``rules checked``
    lines have been stable since v0.4).
    """
    return {
        "quality_signal": _parse_int_after(r"Quality:\s*(\d+)", output),
        "rules_checked": _parse_int_after(
            r"sentrux check\s*[-—]+\s*(\d+)\s+rules?\s+checked", output
        ),
        "files_kept": _parse_int_after(
            r"git ls-files:\s*\d+\s+total,\s*(\d+)\s+kept", output
        ),
        "import_edges": _parse_int_after(r"\|\s*(\d+)\s+import,", output),
        "call_edges": _parse_int_after(r",\s*(\d+)\s+call,", output),
        "inherit_edges": _parse_int_after(r",\s*(\d+)\s+inherit\s+edges", output),
    }


def _build_row(
    timestamp: str,
    commit_sha: str,
    parsed: dict[str, str],
    exit_code: int,
) -> str:
    """Assemble one markdown table row from parsed fields and metadata."""
    rules_pass = "true" if exit_code == 0 else "false"
    cells = [
        timestamp,
        commit_sha,
        parsed["quality_signal"],
        parsed["rules_checked"],
        rules_pass,
        parsed["files_kept"],
        parsed["import_edges"],
        parsed["call_edges"],
        parsed["inherit_edges"],
        str(exit_code),
    ]
    return "| " + " | ".join(cells) + " |\n"


def _ensure_history_file(history_path: Path) -> None:
    """Create the parent dir and header block when missing; otherwise no-op."""
    history_path.parent.mkdir(parents=True, exist_ok=True)
    if history_path.exists():
        return
    history_path.write_text(_header_block(), encoding="utf-8")


def _build_report_payload(
    timestamp: str,
    commit_sha: str,
    parsed: dict[str, str],
    exit_code: int,
    raw_output: str,
) -> dict[str, Any]:
    """Assemble the per-run JSON payload (canonical, machine-readable)."""
    return {
        "timestamp": timestamp,
        "commit_sha": commit_sha if commit_sha != _NULL_CELL else None,
        "exit_code": exit_code,
        "rules": {
            "checked": _to_json_number(parsed["rules_checked"]),
            "passed": exit_code == 0,
        },
        "quality_signal": _to_json_number(parsed["quality_signal"]),
        "graph": {
            "files_kept": _to_json_number(parsed["files_kept"]),
            "import_edges": _to_json_number(parsed["import_edges"]),
            "call_edges": _to_json_number(parsed["call_edges"]),
            "inherit_edges": _to_json_number(parsed["inherit_edges"]),
        },
        "raw_output": raw_output,
    }


def _render_report_md(payload: dict[str, Any]) -> str:
    """Render the per-run report as a small human-readable Markdown document."""
    rules_glyph = "PASS" if payload["rules"]["passed"] else "FAIL"
    quality = payload["quality_signal"]
    quality_str = "—" if quality is None else f"{quality} / 10000"
    graph = payload["graph"]
    sha = payload["commit_sha"] or "—"
    lines = [
        f"# Sentrux report — {payload['timestamp']}",
        "",
        f"- **Commit:** `{sha}`",
        f"- **Exit code:** {payload['exit_code']}  ({rules_glyph})",
        f"- **Quality signal:** {quality_str}",
        f"- **Rules checked:** {payload['rules']['checked'] if payload['rules']['checked'] is not None else '—'}",
        "",
        "## Graph",
        "",
        f"- Files indexed: {graph['files_kept'] if graph['files_kept'] is not None else '—'}",
        f"- Import edges: {graph['import_edges'] if graph['import_edges'] is not None else '—'}",
        f"- Call edges: {graph['call_edges'] if graph['call_edges'] is not None else '—'}",
        f"- Inherit edges: {graph['inherit_edges'] if graph['inherit_edges'] is not None else '—'}",
        "",
        "## Raw `sentrux check` output",
        "",
        "```",
        payload["raw_output"].rstrip() or "(no output captured)",
        "```",
        "",
    ]
    return "\n".join(lines)


def _write_per_run_report(
    reports_dir: Path, filename_ts: str, payload: dict[str, Any]
) -> None:
    """Write the JSON + MD pair for one run; both filenames share the timestamp."""
    json_path = reports_dir / f"{_REPORT_FILENAME_PREFIX}{filename_ts}.json"
    md_path = reports_dir / f"{_REPORT_FILENAME_PREFIX}{filename_ts}.md"
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    md_path.write_text(_render_report_md(payload), encoding="utf-8")


def append_row(repo_root: Path, sentrux_bin: str) -> int:
    """Top-level orchestration: run check, parse, write triple, return exit code.

    Writes three artifacts (per-run JSON, per-run MD, log row) in one
    atomic-ish sequence so a partial failure cannot land an inconsistent
    state. Returns the sentrux process exit code so the caller (CI, hook,
    interactive shell) can fail-fast on rule violations while still
    landing the history triple.
    """
    output, exit_code = _run_sentrux_check(sentrux_bin, repo_root)
    parsed = (
        _parse_sentrux_output(output)
        if output
        else {col: _NULL_CELL for col in _NUMERIC_FIELDS}
    )
    timestamp = _utc_now_iso()
    commit_sha = _git_commit_sha(repo_root)
    payload = _build_report_payload(
        timestamp=timestamp,
        commit_sha=commit_sha,
        parsed=parsed,
        exit_code=exit_code,
        raw_output=output,
    )
    reports_dir = repo_root / _METRICS_REPORTS_DIRNAME
    reports_dir.mkdir(parents=True, exist_ok=True)
    _write_per_run_report(reports_dir, _filename_timestamp(), payload)
    history_path = reports_dir / _HISTORY_FILENAME
    _ensure_history_file(history_path)
    row = _build_row(
        timestamp=timestamp,
        commit_sha=commit_sha,
        parsed=parsed,
        exit_code=exit_code,
    )
    with history_path.open("a", encoding="utf-8") as fh:
        fh.write(row)
    return exit_code


def _parse_args(argv: list[str]) -> argparse.Namespace:
    """Return the parsed CLI namespace; ``append`` is the only subcommand for now."""
    parser = argparse.ArgumentParser(
        description="Append a row to .ai-state/metrics_reports/SENTRUX_HISTORY.md",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    appender = sub.add_parser("append", help="Run sentrux check and append a row.")
    appender.add_argument(
        "--repo-root",
        default=".",
        help="Path to the repository root (default: cwd).",
    )
    appender.add_argument(
        "--sentrux-bin",
        default="sentrux",
        help="Path or name of the sentrux binary (default: sentrux on PATH).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns the sentrux check exit code (0 = pass)."""
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    repo_root = Path(args.repo_root).resolve()
    return append_row(repo_root=repo_root, sentrux_bin=args.sentrux_bin)


if __name__ == "__main__":
    raise SystemExit(main())
