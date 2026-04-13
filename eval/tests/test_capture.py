"""Tests for baseline capture — Phoenix is monkey-patched via injected summary."""

from __future__ import annotations

from pathlib import Path

from praxion_evals.regression.baselines import load_baseline
from praxion_evals.regression.capture import (
    capture_and_write,
    capture_baseline,
    default_output_path,
)
from praxion_evals.regression.trace_reader import TraceSummary


def test_capture_populates_numeric_fields_from_injected_summary(tmp_path: Path):
    summary = TraceSummary(
        project_name="demo",
        span_count=142,
        tool_call_count=37,
        agent_count=5,
        duration_ms_p50=1250.0,
        duration_ms_p95=4800.0,
    )
    baseline = capture_baseline(
        task_slug="demo",
        repo_root=tmp_path,
        current_summary=summary,
    )
    assert baseline.task_slug == "demo"
    assert baseline.span_count == 142
    assert baseline.tool_call_count == 37
    assert baseline.agent_count == 5
    assert baseline.duration_ms_p95 == 4800.0
    assert baseline.has_numeric_fields is True


def test_capture_discovers_deliverables_from_task_dir(tmp_path: Path):
    task_dir = tmp_path / ".ai-work" / "demo"
    task_dir.mkdir(parents=True)
    (task_dir / "SYSTEMS_PLAN.md").write_text("x", encoding="utf-8")
    (task_dir / "WIP.md").write_text("x", encoding="utf-8")
    (task_dir / "notes.txt").write_text("ignored", encoding="utf-8")

    summary = TraceSummary(project_name="demo", span_count=1)
    baseline = capture_baseline(
        task_slug="demo",
        repo_root=tmp_path,
        current_summary=summary,
    )
    assert ".ai-work/demo/SYSTEMS_PLAN.md" in baseline.expected_deliverables
    assert ".ai-work/demo/WIP.md" in baseline.expected_deliverables
    assert not any(".txt" in d for d in baseline.expected_deliverables)


def test_capture_handles_missing_task_dir(tmp_path: Path):
    summary = TraceSummary(project_name="demo", span_count=1)
    baseline = capture_baseline(
        task_slug="ghost",
        repo_root=tmp_path,
        current_summary=summary,
    )
    assert baseline.expected_deliverables == ()


def test_capture_with_empty_phoenix_leaves_numeric_fields_none(tmp_path: Path):
    summary = TraceSummary(project_name="demo", span_count=0, notes=("no-spans-found",))
    baseline = capture_baseline(
        task_slug="demo",
        repo_root=tmp_path,
        current_summary=summary,
    )
    assert baseline.has_numeric_fields is False
    assert baseline.span_count is None


def test_capture_and_write_round_trips(tmp_path: Path):
    output = tmp_path / "baselines" / "demo.json"
    summary = TraceSummary(
        project_name="demo",
        span_count=50,
        tool_call_count=10,
    )
    written = capture_and_write(
        task_slug="demo",
        output_path=output,
        repo_root=tmp_path,
        current_summary=summary,
    )
    assert output.exists()
    loaded = load_baseline(output)
    assert loaded.task_slug == written.task_slug
    assert loaded.span_count == 50
    assert loaded.tool_call_count == 10


def test_default_output_path_uses_convention(tmp_path: Path):
    path = default_output_path("demo", repo_root=tmp_path)
    assert path == tmp_path / ".ai-state" / "evals" / "baselines" / "demo.json"
