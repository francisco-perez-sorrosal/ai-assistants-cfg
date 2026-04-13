"""Regression runner: ensures the comparator never tries to write back to Phoenix."""

from __future__ import annotations

from pathlib import Path

import pytest

from praxion_evals.regression.baselines import (
    BaselineSummary,
    utc_now,
    write_baseline,
)
from praxion_evals.regression.runner import run_regression
from praxion_evals.regression.trace_reader import TraceSummary


def test_runner_with_injected_summary_reports_drift(tmp_path: Path):
    baseline = BaselineSummary(
        task_slug="demo",
        captured_at=utc_now(),
        span_count=100,
    )
    path = tmp_path / "baseline.json"
    write_baseline(baseline, path)

    current = TraceSummary(project_name="demo", span_count=300)
    result = run_regression(path, current_summary=current)
    assert result.has_drift is True
    assert result.task_slug == "demo"


def test_runner_never_calls_phoenix_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """If the runner ever tries to mutate Phoenix, explode loudly."""
    baseline = BaselineSummary(
        task_slug="demo",
        captured_at=utc_now(),
        span_count=100,
    )
    path = tmp_path / "baseline.json"
    write_baseline(baseline, path)

    # Monkey-patch px.Client.log_evaluations to fail loudly if called.
    import sys
    from types import SimpleNamespace

    def _fail(*_args: object, **_kwargs: object):
        raise AssertionError("regression eval must not call log_evaluations")

    fake_client = SimpleNamespace(log_evaluations=_fail, get_spans_dataframe=lambda **_: None)
    monkeypatch.setitem(
        sys.modules,
        "phoenix",
        SimpleNamespace(Client=lambda *_a, **_k: fake_client),
    )

    current = TraceSummary(project_name="demo", span_count=100)
    result = run_regression(path, current_summary=current)
    assert result.has_drift is False


def test_runner_flags_missing_expected_deliverables(tmp_path: Path):
    baseline = BaselineSummary(
        task_slug="demo",
        captured_at=utc_now(),
        span_count=100,
        expected_deliverables=(
            ".ai-work/demo/SYSTEMS_PLAN.md",
            ".ai-work/demo/MISSING.md",
        ),
    )
    baseline_path = tmp_path / "baseline.json"
    write_baseline(baseline, baseline_path)

    # Only SYSTEMS_PLAN.md exists; MISSING.md is absent.
    (tmp_path / ".ai-work" / "demo").mkdir(parents=True)
    (tmp_path / ".ai-work" / "demo" / "SYSTEMS_PLAN.md").write_text("x", encoding="utf-8")

    current = TraceSummary(project_name="demo", span_count=100)
    result = run_regression(baseline_path, current_summary=current, repo_root=tmp_path)

    assert result.has_drift is True
    assert any("missing deliverable" in f and "MISSING.md" in f for f in result.findings)
    assert not any("SYSTEMS_PLAN.md" in f for f in result.findings)


def test_runner_skips_deliverable_check_when_repo_root_absent(tmp_path: Path):
    baseline = BaselineSummary(
        task_slug="demo",
        captured_at=utc_now(),
        span_count=100,
        expected_deliverables=(".ai-work/demo/ANYTHING.md",),
    )
    baseline_path = tmp_path / "baseline.json"
    write_baseline(baseline, baseline_path)

    current = TraceSummary(project_name="demo", span_count=100)
    # No repo_root → deliverables not checked, so no findings.
    result = run_regression(baseline_path, current_summary=current)
    assert result.has_drift is False
