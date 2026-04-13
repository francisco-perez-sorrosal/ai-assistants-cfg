"""Top-level regression eval entrypoint — never mutates traces."""

from __future__ import annotations

from pathlib import Path

from praxion_evals.regression.baselines import BaselineSummary, load_baseline
from praxion_evals.regression.diff import DiffResult, compare_summaries
from praxion_evals.regression.trace_reader import (
    TraceSummary,
    read_current_summary,
)


def _missing_deliverables(baseline: BaselineSummary, repo_root: Path) -> tuple[str, ...]:
    """Return expected deliverables from the baseline that are absent on disk."""
    missing: list[str] = []
    for rel in baseline.expected_deliverables:
        if not (repo_root / rel).exists():
            missing.append(rel)
    return tuple(missing)


def run_regression(
    baseline_path: Path,
    current_summary: TraceSummary | None = None,
    project_name: str | None = None,
    repo_root: Path | None = None,
) -> DiffResult:
    """Load a baseline, fetch (or accept) a current summary, and compare.

    ``current_summary`` exists so tests can inject a synthetic TraceSummary
    without touching Phoenix. In production, callers pass only ``baseline_path``
    and the function pulls the current summary lazily.

    ``repo_root`` enables the on-disk deliverable check -- if the baseline has
    ``expected_deliverables`` and a repo root is supplied, missing files appear
    as drift findings. Semantics of ``expected_phases`` are underspecified
    (phase names vs. Phoenix AGENT span names); phase validation is deferred.
    """
    baseline: BaselineSummary = load_baseline(baseline_path)
    if current_summary is None:
        summary = read_current_summary(project_name or baseline.task_slug)
    else:
        summary = current_summary

    numeric_diff = compare_summaries(summary, baseline)
    findings: list[str] = list(numeric_diff.findings)

    if repo_root is not None:
        for rel in _missing_deliverables(baseline, repo_root):
            findings.append(f"missing deliverable: {rel}")

    return DiffResult(task_slug=baseline.task_slug, findings=tuple(findings))
