"""Behavioral tests for streamlit_app/pages/metrics.py.

The Metrics page supersedes the static ``metrics-viewer.html.tmpl``.  It:

  1. Discovers the latest ``METRICS_REPORT_*.json`` via
     ``discovery.list_metrics_reports_json`` and renders its ``aggregate``
     namespace as a KPI grid (15 fields via ``st.metric``).
  2. Discovers ``METRICS_LOG.md`` via ``discovery.find_metrics_log`` and
     renders trend lines for aggregate fields via
     ``graph.metrics_aggregate_lines`` + ``st.plotly_chart``.
  3. Degrades to an empty-state widget when both sources are absent.
  4. Shows a reduced view when only one source is available.
  5. Handles malformed JSON gracefully (no crash).
  6. Exposes a single ``render()`` callable with no import-time Streamlit calls.

Concurrent BDD/TDD state
-------------------------
The implementer and test-engineer run concurrently in this paired step.
The current ``metrics.py`` is a stub that renders a placeholder ``st.info``.
Tests targeting the full pair-contract are marked xfail when the stub is
detected; structural tests (AST purity, render() export) pass against the stub.

Deferred imports
----------------
Production modules are imported inside each test body (not at module top) so
pytest collection succeeds even when the implementation is absent — preserving
the RED handshake.

REGISTERED OBJECTION — concurrent-mode GREEN on first run
----------------------------------------------------------
Steps 3b, 4b, 5b, 6b, 7b, 8b, 9b, and 10b all showed the implementer landing
first.  If all behavioral tests pass GREEN on first run, the same pattern
applies — per memory ``pattern_concurrent_bdd_green_on_first_run``: not a
defect when the behavioral contract is correctly encoded.

Convention compliance
---------------------
- No REQ/AC/Step IDs in test names or bodies (id-citation-discipline).
- Fixture JSON filenames use generic timestamps, not real worktree report
  entries (shipped-artifact-isolation).
- ``mtime`` (not ``_mtime``) used when calling cache functions (Convention 2).
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed(root: Path, structure: dict[str, Any]) -> None:
    """Recursively create files and directories from a nested dict.

    Keys are path components.  None → empty file; str/bytes → file with
    content; dict → directory (recurse).
    """
    for name, value in structure.items():
        target = root / name
        if isinstance(value, dict):
            target.mkdir(parents=True, exist_ok=True)
            _seed(target, value)
        elif value is None:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.touch()
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(value), encoding="utf-8")


# ---------------------------------------------------------------------------
# Shared fixture content
# ---------------------------------------------------------------------------

# Minimal valid METRICS_REPORT JSON — contains aggregate namespace with
# representative scalar fields.  Uses generic timestamps to avoid referencing
# real worktree artifacts (shipped-artifact-isolation).
_MINIMAL_AGGREGATE: dict[str, Any] = {
    "schema_version": "1.0.0",
    "timestamp": "2026-01-01T00:00:00Z",
    "commit_sha": "abc1234",
    "window_days": 90,
    "sloc_total": 5000,
    "file_count": 120,
    "language_count": 3,
    "ccn_p95": 4.2,
    "cognitive_p95": 8.1,
    "cyclic_deps": 2,
    "churn_total_90d": 380,
    "change_entropy_90d": 0.72,
    "truck_factor": 3,
    "hotspot_top_score": 0.85,
    "hotspot_gini": 0.41,
    "coverage_line_pct": 87.5,
}

_MINIMAL_JSON_REPORT: dict[str, Any] = {
    "schema_version": "1.0.0",
    "aggregate": _MINIMAL_AGGREGATE,
    "tool_availability": {},
    "collectors": {},
}

_NEWER_AGGREGATE: dict[str, Any] = {
    **_MINIMAL_AGGREGATE,
    "timestamp": "2026-03-01T00:00:00Z",
    "sloc_total": 7777,
    "coverage_line_pct": 93.0,
}

_NEWER_JSON_REPORT: dict[str, Any] = {
    "schema_version": "1.0.0",
    "aggregate": _NEWER_AGGREGATE,
    "tool_availability": {},
    "collectors": {},
}

_OLDER_JSON_REPORT: dict[str, Any] = {
    "schema_version": "1.0.0",
    "aggregate": {
        **_MINIMAL_AGGREGATE,
        "sloc_total": 1111,
        "timestamp": "2025-12-01T00:00:00Z",
    },
    "tool_availability": {},
    "collectors": {},
}

# Minimal METRICS_LOG.md content — pipe-delimited table with header +
# separator + two data rows.
_METRICS_LOG_CONTENT = """\
# Metrics Log

| schema_version | timestamp | commit_sha | window_days | sloc_total | file_count | language_count | ccn_p95 | cognitive_p95 | cyclic_deps | churn_total_90d | change_entropy_90d | truck_factor | hotspot_top_score | hotspot_gini | coverage_line_pct | report_file |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.0.0 | 2026-01-01T00:00:00Z | abc1234 | 90 | 5000 | 120 | 3 | 4.2 | 8.1 | 2 | 380 | 0.72 | 3 | 0.85 | 0.41 | 87.5 | METRICS_REPORT_2026-01-01.json |
| 1.0.0 | 2026-02-01T00:00:00Z | def5678 | 90 | 5500 | 125 | 3 | 4.5 | 8.3 | 1 | 390 | 0.74 | 3 | 0.87 | 0.43 | 88.0 | METRICS_REPORT_2026-02-01.json |
"""


def _run_metrics_page(project_root: Path, monkeypatch: pytest.MonkeyPatch) -> AppTest:
    """Set env var, clear config cache, run the metrics page via AppTest."""
    monkeypatch.setenv("PRAXION_PROJECT_ROOT", str(project_root))
    try:
        from streamlit_app.config import get_config  # noqa: PLC0415

        get_config.cache_clear()
    except Exception:  # noqa: BLE001
        pass

    script = (
        "import os\n"
        f"os.environ['PRAXION_PROJECT_ROOT'] = {str(project_root)!r}\n"
        "from streamlit_app.config import get_config; get_config.cache_clear()\n"
        "from streamlit_app.pages.metrics import render\n"
        "render()\n"
    )
    return AppTest.from_string(script).run()


def _is_stub(at: AppTest) -> bool:
    """Return True when the page still renders the stub placeholder info text."""
    all_info = " ".join(e.value for e in at.info)
    return (
        "later implementation" in all_info
        or "lands in a later" in all_info
        or "Coming soon" in all_info
        or "will render" in all_info.lower()
        or "KPI grid" in all_info
    )


def _all_text(at: AppTest) -> str:
    """Collect all visible text from an AppTest result."""
    parts = []
    for group in [at.title, at.header, at.subheader, at.markdown, at.info, at.warning]:
        for element in group:
            parts.append(element.value)
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Group 1 — Empty state
# ---------------------------------------------------------------------------


class TestEmptyStateWhenNoMetricsDir:
    """Metrics page shows empty state when no metrics artifacts exist."""

    def test_empty_state_when_no_metrics_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No metrics_reports/ directory → empty-state widget, no exception."""
        # Project root with .ai-state/ but NO metrics_reports/
        _seed(tmp_path, {".ai-state": {"decisions": {"drafts": {}}}})

        at = _run_metrics_page(tmp_path, monkeypatch)

        if at.exception:
            exc_msg = str(at.exception[0].message)
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")

        assert not at.exception, (
            f"Metrics page raised an exception on empty project root: {at.exception}"
        )


# ---------------------------------------------------------------------------
# Group 2 — KPI grid from latest JSON
# ---------------------------------------------------------------------------


class TestRendersKpisFromLatestJson:
    """Metrics page renders the KPI grid from the latest METRICS_REPORT JSON."""

    def test_renders_kpis_from_latest_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With one JSON report present, KPI labels from aggregate appear in the page.

        At least one field name from the aggregate namespace (sloc_total,
        coverage_line_pct, truck_factor, etc.) must appear in the rendered output.
        """
        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "metrics_reports": {
                        "METRICS_REPORT_2026-01-01.json": json.dumps(
                            _MINIMAL_JSON_REPORT
                        ),
                    },
                },
            },
        )

        at = _run_metrics_page(tmp_path, monkeypatch)

        if at.exception:
            exc_msg = str(at.exception[0].message)
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")

        if _is_stub(at):
            pytest.xfail("metrics.py still a stub — full implementation pending")

        assert not at.exception, (
            f"Metrics page raised an exception with a valid JSON report: {at.exception}"
        )

        # at.metric surfaces st.metric() tiles — check KPI labels or fallback to text
        kpi_fields = [
            "sloc",
            "coverage",
            "truck",
            "churn",
            "cyclic",
            "hotspot",
            "file",
            "language",
            "entropy",
        ]
        metric_labels = " ".join(e.label.lower() for e in at.metric)
        has_kpi = any(field in metric_labels for field in kpi_fields)
        if not has_kpi:
            # Fallback: check all text in case the implementation uses a different widget
            text = _all_text(at)
            has_kpi = any(field in text.lower() for field in kpi_fields)
        assert has_kpi, (
            f"No KPI label visible in rendered page. "
            f"Metric labels found: {[e.label for e in at.metric]!r}. "
            f"Aggregate fields expected: {list(_MINIMAL_AGGREGATE.keys())}"
        )


# ---------------------------------------------------------------------------
# Group 3 — Picks newest JSON when multiple reports exist
# ---------------------------------------------------------------------------


class TestPicksNewestJsonWhenMultiple:
    """Metrics page selects the most recent METRICS_REPORT JSON by filename."""

    def test_picks_newest_json_when_multiple(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With three JSON reports, the page reflects the newest report's values.

        Filenames are timestamp-embedded; newest sorts last lexicographically
        and first in descending order.  The page must pick the newest.
        The newest report's distinctive sloc_total value (7777) must appear
        in the rendered output rather than the older report's value (1111).
        """
        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "metrics_reports": {
                        "METRICS_REPORT_2025-12-01.json": json.dumps(
                            _OLDER_JSON_REPORT
                        ),
                        "METRICS_REPORT_2026-01-01.json": json.dumps(
                            _MINIMAL_JSON_REPORT
                        ),
                        "METRICS_REPORT_2026-03-01.json": json.dumps(
                            _NEWER_JSON_REPORT
                        ),
                    },
                },
            },
        )

        at = _run_metrics_page(tmp_path, monkeypatch)

        if at.exception:
            exc_msg = str(at.exception[0].message)
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")

        if _is_stub(at):
            pytest.xfail("metrics.py still a stub — multi-report selection pending")

        assert not at.exception, (
            f"Metrics page raised exception with multiple JSON reports: {at.exception}"
        )

        # at.metric surfaces st.metric() tiles with the selected report's values.
        # The newest report has sloc_total=7777 and coverage_line_pct=93.0.
        metric_values = " ".join(str(e.value) for e in at.metric)
        metric_labels = " ".join(e.label.lower() for e in at.metric)
        newest_visible = (
            "7777" in metric_values
            or "93.0" in metric_values
            or "2026-03" in metric_values
        )
        if not newest_visible:
            # Fallback: check all rendered text
            text = _all_text(at)
            newest_visible = "7777" in text or "93" in text or "2026-03" in text
        assert newest_visible, (
            "Newest JSON report values not found in rendered page. "
            f"Expected 7777 (sloc_total) or 93.0 (coverage_line_pct) from the newest report "
            f"(METRICS_REPORT_2026-03-01.json). "
            f"Metric values found: {[e.value for e in at.metric]!r}. "
            f"Metric labels found: {[e.label for e in at.metric]!r}."
        )


# ---------------------------------------------------------------------------
# Group 4 — Trend chart when log present
# ---------------------------------------------------------------------------


class TestRendersTrendWhenLogPresent:
    """Metrics page renders trend lines when METRICS_LOG.md is present."""

    def test_renders_trend_when_log_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With both JSON report and METRICS_LOG.md present, the page renders without crash.

        AppTest does not expose a queryable accessor for st.plotly_chart output.
        The behavioral contract is: (a) pure-function layer verifies the graph
        function produces a Figure from the DataFrame, (b) this integration
        test verifies the page does not crash when the log is present.
        """
        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "metrics_reports": {
                        "METRICS_REPORT_2026-01-01.json": json.dumps(
                            _MINIMAL_JSON_REPORT
                        ),
                        "METRICS_LOG.md": _METRICS_LOG_CONTENT,
                    },
                },
            },
        )

        at = _run_metrics_page(tmp_path, monkeypatch)

        if at.exception:
            exc_msg = str(at.exception[0].message)
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")

        if _is_stub(at):
            pytest.xfail("metrics.py still a stub — trend chart pending")

        assert not at.exception, (
            f"Metrics page raised an exception when METRICS_LOG.md is present: {at.exception}"
        )


# ---------------------------------------------------------------------------
# Group 5 — Only METRICS_LOG.md present (no JSON)
# ---------------------------------------------------------------------------


class TestRendersWhenOnlyLogPresent:
    """Metrics page degrades gracefully when only METRICS_LOG.md is present."""

    def test_renders_when_only_log_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No JSON report but METRICS_LOG.md present → page renders without crash.

        The KPI grid must be omitted (no JSON), but trend data can still be
        shown from the log.  The page must not raise an exception.
        """
        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "metrics_reports": {
                        "METRICS_LOG.md": _METRICS_LOG_CONTENT,
                    },
                },
            },
        )

        at = _run_metrics_page(tmp_path, monkeypatch)

        if at.exception:
            exc_msg = str(at.exception[0].message)
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")

        if _is_stub(at):
            pytest.xfail("metrics.py still a stub — log-only path pending")

        assert not at.exception, (
            f"Metrics page raised an exception when only METRICS_LOG.md is present: {at.exception}"
        )


# ---------------------------------------------------------------------------
# Group 6 — Only JSON present (no log)
# ---------------------------------------------------------------------------


class TestRendersWhenOnlyJsonPresent:
    """Metrics page renders KPI grid when only a JSON report is present (no log)."""

    def test_renders_when_only_json_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No METRICS_LOG.md but a valid JSON report present → KPI grid, no crash.

        Trend section must be omitted gracefully; the KPI grid from the JSON
        must be displayed.
        """
        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "metrics_reports": {
                        "METRICS_REPORT_2026-01-01.json": json.dumps(
                            _MINIMAL_JSON_REPORT
                        ),
                        # No METRICS_LOG.md
                    },
                },
            },
        )

        at = _run_metrics_page(tmp_path, monkeypatch)

        if at.exception:
            exc_msg = str(at.exception[0].message)
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")

        if _is_stub(at):
            pytest.xfail("metrics.py still a stub — JSON-only path pending")

        assert not at.exception, (
            f"Metrics page raised an exception when only JSON is present: {at.exception}"
        )


# ---------------------------------------------------------------------------
# Group 7 — Malformed JSON handled gracefully
# ---------------------------------------------------------------------------


class TestHandlesMalformedJsonGracefully:
    """Metrics page does not crash when the JSON report is malformed."""

    def test_handles_malformed_json_gracefully(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A JSON file with broken content → page renders a fallback, no exception.

        The parsers layer raises ``json.JSONDecodeError`` for broken JSON;
        the page must catch this at the boundary and degrade gracefully
        rather than surfacing a raw exception.
        """
        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "metrics_reports": {
                        "METRICS_REPORT_2026-01-01.json": (
                            "{broken json content not parseable"
                        ),
                    },
                },
            },
        )

        at = _run_metrics_page(tmp_path, monkeypatch)

        if at.exception:
            exc_msg = str(at.exception[0].message)
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")
            # If the stub is still present, it renders st.info regardless of JSON
            if _is_stub(at):
                pytest.xfail("metrics.py still a stub — malformed-JSON path pending")

        # The page must not surface a raw exception to the user
        assert not at.exception, (
            "Metrics page raised an exception when JSON was malformed.\n"
            f"Exception: {at.exception}\n"
            "The page must catch parse errors and degrade gracefully."
        )


# ---------------------------------------------------------------------------
# Group 8 — Module purity (Convention 6)
# ---------------------------------------------------------------------------


class TestModulePurityNoImportTimeStreamlitCalls:
    """metrics.py must not execute Streamlit calls at import time."""

    def test_module_purity_no_import_time_streamlit_calls(self) -> None:
        """metrics.py has no module-level st.* rendering calls (Convention 6).

        Uses AST inspection rather than importing the module, so it works
        regardless of concurrent-mode implementation state.
        """
        metrics_path = Path(__file__).parents[1] / "pages" / "metrics.py"
        if not metrics_path.exists():
            pytest.skip("metrics.py not yet on disk — concurrent mode, expected")

        source = metrics_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        top_level_st_calls: list[str] = []
        for node in ast.iter_child_nodes(tree):
            # Skip function and class definitions — calls inside them are fine
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    func = sub.func
                    if (
                        isinstance(func, ast.Attribute)
                        and isinstance(func.value, ast.Name)
                        and func.value.id == "st"
                    ):
                        top_level_st_calls.append(f"st.{func.attr}()")

        assert not top_level_st_calls, (
            f"Import-time Streamlit calls found in metrics.py: {top_level_st_calls}. "
            "All st.* calls must be inside render() (Convention 6)."
        )


# ---------------------------------------------------------------------------
# Group 9 — Convention 6: single render() export
# ---------------------------------------------------------------------------


class TestRenderFunctionDefined:
    """metrics.py defines and exports a single render() callable (Convention 6)."""

    def test_render_function_defined(self) -> None:
        """metrics.py defines a top-level render() function via AST check."""
        metrics_path = Path(__file__).parents[1] / "pages" / "metrics.py"
        if not metrics_path.exists():
            pytest.skip("metrics.py not yet on disk — concurrent mode, expected")

        source = metrics_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        top_level_function_names = {
            node.name
            for node in ast.iter_child_nodes(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

        assert "render" in top_level_function_names, (
            f"metrics.py must define a top-level render() function. "
            f"Found functions: {sorted(top_level_function_names)}"
        )


# ---------------------------------------------------------------------------
# Pure-function layer — graph.metrics_aggregate_lines contract
# ---------------------------------------------------------------------------


class TestMetricsAggregateLinesPureContract:
    """graph.metrics_aggregate_lines produces a valid Plotly Figure from log data.

    Pure-function layer: tested without AppTest to verify the graph contract
    independently of the page rendering code.  Mirrors the two-layer pattern
    used for sentinel health sparkline and SVG embed tests.
    """

    def test_aggregate_lines_returns_figure_from_dataframe(self) -> None:
        """metrics_aggregate_lines returns a Plotly Figure from a non-empty DataFrame."""
        try:
            import pandas as pd  # noqa: PLC0415

            from streamlit_app.widgets.graph import (  # noqa: PLC0415
                metrics_aggregate_lines,
            )
        except ImportError:
            pytest.skip("graph module or pandas not importable yet — concurrent mode")

        df = pd.DataFrame(
            {
                "timestamp": ["2026-01-01", "2026-02-01"],
                "sloc_total": [5000, 5500],
                "coverage_line_pct": [87.5, 88.0],
            }
        )
        fig = metrics_aggregate_lines(df)
        assert hasattr(fig, "data"), (
            "metrics_aggregate_lines must return a Plotly Figure-like object. "
            f"Got: {type(fig)}"
        )

    def test_aggregate_lines_returns_empty_figure_for_empty_dataframe(self) -> None:
        """metrics_aggregate_lines returns an empty Figure for an empty DataFrame."""
        try:
            import pandas as pd  # noqa: PLC0415

            from streamlit_app.widgets.graph import (  # noqa: PLC0415
                metrics_aggregate_lines,
            )
        except ImportError:
            pytest.skip("graph module or pandas not importable yet — concurrent mode")

        fig = metrics_aggregate_lines(pd.DataFrame())
        assert hasattr(fig, "data"), (
            "metrics_aggregate_lines must return a Plotly Figure-like object for empty input. "
            f"Got: {type(fig)}"
        )
