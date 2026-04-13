"""Capture a baseline snapshot from live Phoenix traces and on-disk artifacts.

Populates a ``BaselineSummary`` with the Phoenix-derived numeric fields the
diff engine actually compares (span_count, tool_call_count, agent_count,
duration_ms_p50, duration_ms_p95) plus the expected deliverables discovered
under ``.ai-work/<task-slug>/``. The resulting JSON is what ``run_regression``
needs to produce meaningful drift findings.

Contract: read-only against both Phoenix and the filesystem. Never mutates
traces; writes only the baseline JSON when ``write_path`` is supplied.
"""

from __future__ import annotations

from pathlib import Path

from praxion_evals.regression.baselines import (
    BaselineSummary,
    utc_now,
    write_baseline,
)
from praxion_evals.regression.trace_reader import (
    TraceSummary,
    read_current_summary,
)


def _discover_deliverables(task_slug: str, repo_root: Path) -> tuple[str, ...]:
    """Return repo-relative paths of ``.md`` artifacts under the task dir."""
    task_dir = repo_root / ".ai-work" / task_slug
    if not task_dir.is_dir():
        return ()
    paths = sorted(p for p in task_dir.glob("*.md") if p.is_file())
    return tuple(str(p.relative_to(repo_root)) for p in paths)


def capture_baseline(
    task_slug: str,
    repo_root: Path | None = None,
    current_summary: TraceSummary | None = None,
) -> BaselineSummary:
    """Build a ``BaselineSummary`` from a current Phoenix summary + repo state.

    ``current_summary`` exists so tests can inject a synthetic TraceSummary
    without touching Phoenix. In production, callers pass only ``task_slug``
    and this function pulls the summary lazily.
    """
    root = repo_root or Path.cwd()
    summary = current_summary if current_summary is not None else read_current_summary(task_slug)

    return BaselineSummary(
        task_slug=task_slug,
        captured_at=utc_now(),
        expected_deliverables=_discover_deliverables(task_slug, root),
        span_count=summary.span_count or None,
        tool_call_count=summary.tool_call_count or None,
        agent_count=summary.agent_count or None,
        duration_ms_p50=summary.duration_ms_p50,
        duration_ms_p95=summary.duration_ms_p95,
    )


def capture_and_write(
    task_slug: str,
    output_path: Path,
    repo_root: Path | None = None,
    current_summary: TraceSummary | None = None,
) -> BaselineSummary:
    """Capture a baseline and persist it to ``output_path``."""
    baseline = capture_baseline(
        task_slug=task_slug,
        repo_root=repo_root,
        current_summary=current_summary,
    )
    write_baseline(baseline, output_path)
    return baseline


def default_output_path(task_slug: str, repo_root: Path | None = None) -> Path:
    """Convention: ``<repo_root>/.ai-state/evals/baselines/<slug>.json``."""
    root = repo_root or Path.cwd()
    return root / ".ai-state" / "evals" / "baselines" / f"{task_slug}.json"
