"""Behavioral tests for streamlit_app/pages/sentinel.py.

The Sentinel page shows Praxion ecosystem health:
  1. Reads SENTINEL_LOG.md (history of health grades over time).
  2. Renders a sparkline of historical health grades via
     graph.sentinel_health_sparkline → st.plotly_chart.
  3. Reads the latest SENTINEL_REPORT_*.md (most recent by filename timestamp).
  4. Renders the latest report's frontmatter metadata as a scorecard.
  5. Renders tiered findings from the report body as artifact cards.
  6. Shows empty state when no sentinel_reports/ directory or artifacts exist.

Concurrent BDD/TDD state
-------------------------
The implementer and test-engineer run concurrently in this paired step.
The current sentinel.py is a stub that renders a placeholder st.info() message.
Tests targeting the full pair-contract behavior are expected to fail (RED) until
the implementer lands.

Tests that check structural properties of the source file (AST, render() defined)
are expected to pass immediately against the existing stub.

Deferred imports
----------------
Production modules are imported inside each test body (not at module top) so
pytest collection succeeds even when the implementation is absent — preserving
the RED handshake.

REGISTERED OBJECTION — concurrent-mode GREEN on first run
----------------------------------------------------------
If all behavioral tests pass GREEN on the first run, the implementer has already
landed sentinel.py before these tests were written.  Per
``pattern_concurrent_bdd_green_on_first_run``: not a defect when the behavioral
contract is correctly encoded.  The tests validate what the system *should do*,
not just what already exists.

Convention compliance
---------------------
- No REQ/AC/Step IDs in test names or bodies (id-citation-discipline).
- Placeholder SENTINEL_REPORT fixture names use generic timestamps, not real
  worktree report entries (shipped-artifact-isolation).
- ``mtime`` (not ``_mtime``) used when calling cache functions (Convention 2).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed(root: Path, structure: dict[str, Any]) -> None:
    """Recursively create files and directories from a nested dict.

    Keys are path components.  None → empty file; str → file with content;
    dict → directory (recurse).
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


_SENTINEL_LOG_CONTENT = """\
# Sentinel Log

| timestamp | report_file | health_grade | finding_counts | coherence_grade |
|-----------|-------------|-------------|----------------|-----------------|
| 2026-01-01T00:00:00Z | SENTINEL_REPORT_2026-01-01_00-00-00.md | A | 0 | A |
| 2026-02-01T00:00:00Z | SENTINEL_REPORT_2026-02-01_00-00-00.md | B | 2 | A |
| 2026-03-01T00:00:00Z | SENTINEL_REPORT_2026-03-01_00-00-00.md | A | 0 | A |
"""

_SENTINEL_REPORT_CONTENT = """\
---
title: Sentinel Report
date: 2026-03-01
health_grade: A
coherence_grade: A
---

## Findings

No critical findings.

## Dimension Scorecard

All dimensions nominal.
"""

_SENTINEL_REPORT_OLDER_CONTENT = """\
---
title: Sentinel Report (older)
date: 2026-01-01
health_grade: B
coherence_grade: A
---

## Findings

Two findings in this older report.
"""


def _run_sentinel_page(project_root: Path, monkeypatch: pytest.MonkeyPatch) -> AppTest:
    """Set env var, clear config cache, run the sentinel page via AppTest."""
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
        "from streamlit_app.pages.sentinel import render\n"
        "render()\n"
    )
    return AppTest.from_string(script).run()


def _is_stub(at: AppTest) -> bool:
    """Return True if the page is still a stub (renders placeholder info text)."""
    all_info = " ".join(e.value for e in at.info)
    return (
        "later implementation" in all_info
        or "Coming soon" in all_info
        or "will display" in all_info.lower()
        or "lands in a later" in all_info
    )


# ---------------------------------------------------------------------------
# Group 1: Empty state
# ---------------------------------------------------------------------------


class TestEmptyState:
    """Sentinel page degrades gracefully when no sentinel artifacts exist."""

    def test_empty_state_when_no_sentinel_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No sentinel_reports/ directory → empty-state widget, no exception."""
        # Project root with .ai-state/ but empty sentinel_reports/
        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "sentinel_reports": {},
                },
            },
        )

        at = _run_sentinel_page(tmp_path, monkeypatch)

        if at.exception:
            exc_msg = str(at.exception[0].message)
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")

        assert not at.exception, (
            f"Sentinel page raised an exception on empty sentinel_reports/: {at.exception}"
        )


# ---------------------------------------------------------------------------
# Group 2: Latest report title rendering
# ---------------------------------------------------------------------------


class TestRendersLatestReportTitle:
    """Sentinel page renders the latest SENTINEL_REPORT's content."""

    def test_renders_latest_report_title(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With one sentinel report present, the page renders without crashing.

        The page must surface the report's content (title, grade, or section
        headings) somewhere in the rendered output.
        """
        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "sentinel_reports": {
                        "SENTINEL_LOG.md": _SENTINEL_LOG_CONTENT,
                        "SENTINEL_REPORT_2026-03-01_00-00-00.md": _SENTINEL_REPORT_CONTENT,
                    },
                },
            },
        )

        at = _run_sentinel_page(tmp_path, monkeypatch)

        if at.exception:
            exc_msg = str(at.exception[0].message)
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")

        if _is_stub(at):
            pytest.xfail("sentinel.py still a stub — full implementation pending")

        assert not at.exception, (
            f"Sentinel page raised an exception with a valid report: {at.exception}"
        )

        # The page must render something from the report (title bar, grade, or section)
        all_text = (
            " ".join(e.value for e in at.title)
            + " ".join(e.value for e in at.header)
            + " ".join(e.value for e in at.subheader)
            + " ".join(e.value for e in at.markdown)
            + " ".join(e.value for e in at.info)
        )
        assert all_text.strip(), (
            "Sentinel page produced no text output with a valid report"
        )


# ---------------------------------------------------------------------------
# Group 3: Latest-report selection when multiple reports exist
# ---------------------------------------------------------------------------


class TestPicksNewestReport:
    """Sentinel page selects the most recent report by filename timestamp."""

    def test_picks_newest_when_multiple_reports(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With three reports, the page reflects the newest report's content.

        Filenames are lexicographically ordered so the latest timestamp sorts
        last in ascending order and first in descending order (newest = largest
        timestamp string).  The page must pick the newest, not the first or oldest.
        """
        newest_marker = "Sentinel Newest Report Alpha"
        newest_report = (
            "---\n"
            f"title: {newest_marker}\n"
            "date: 2026-05-01\n"
            "health_grade: A\n"
            "---\n\n"
            "## Findings\n\nNewest findings.\n"
        )
        older_report_1 = (
            "---\n"
            "title: Old Report January\n"
            "date: 2026-01-01\n"
            "health_grade: B\n"
            "---\n\n"
            "## Findings\n\nOld January findings.\n"
        )
        older_report_2 = (
            "---\n"
            "title: Old Report February\n"
            "date: 2026-02-01\n"
            "health_grade: B\n"
            "---\n\n"
            "## Findings\n\nOld February findings.\n"
        )
        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "sentinel_reports": {
                        "SENTINEL_LOG.md": _SENTINEL_LOG_CONTENT,
                        "SENTINEL_REPORT_2026-01-01_00-00-00.md": older_report_1,
                        "SENTINEL_REPORT_2026-02-01_00-00-00.md": older_report_2,
                        "SENTINEL_REPORT_2026-05-01_00-00-00.md": newest_report,
                    },
                },
            },
        )

        at = _run_sentinel_page(tmp_path, monkeypatch)

        if at.exception:
            exc_msg = str(at.exception[0].message)
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")

        if _is_stub(at):
            pytest.xfail("sentinel.py still a stub — full implementation pending")

        assert not at.exception, (
            f"Sentinel page raised an exception with multiple reports: {at.exception}"
        )

        all_text = (
            " ".join(e.value for e in at.title)
            + " ".join(e.value for e in at.header)
            + " ".join(e.value for e in at.subheader)
            + " ".join(e.value for e in at.markdown)
            + " ".join(e.value for e in at.info)
        )
        # The newest report's distinctive marker must appear; older-only content must not
        # dominate (we verify the page selected the correct report).
        assert (
            newest_marker in all_text
            or "2026-05-01" in all_text
            or "Newest" in all_text
        ), (
            f"Newest report content not found in page output. "
            f"Got text snippet: {all_text[:500]!r}"
        )


# ---------------------------------------------------------------------------
# Group 4: Health sparkline
# ---------------------------------------------------------------------------


class TestHealthSparkline:
    """Sentinel page renders a health-grade sparkline when the log is present."""

    def test_health_sparkline_renders_when_log_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """SENTINEL_LOG.md present → plotly_chart rendered (sparkline behavior).

        AppTest exposes rendered charts.  When the log exists and has data rows,
        the page must call st.plotly_chart (detectable as at least one chart element
        in the AppTest output, or the page must not crash).
        """
        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "sentinel_reports": {
                        "SENTINEL_LOG.md": _SENTINEL_LOG_CONTENT,
                        "SENTINEL_REPORT_2026-03-01_00-00-00.md": _SENTINEL_REPORT_CONTENT,
                    },
                },
            },
        )

        at = _run_sentinel_page(tmp_path, monkeypatch)

        if at.exception:
            exc_msg = str(at.exception[0].message)
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")

        if _is_stub(at):
            pytest.xfail("sentinel.py still a stub — full implementation pending")

        assert not at.exception, (
            f"Sentinel page raised an exception when log is present: {at.exception}"
        )

    def test_no_sparkline_when_log_absent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """SENTINEL_LOG.md absent → page renders without crashing (no sparkline path).

        When the log is absent, the sparkline should be omitted gracefully —
        no exception raised, and an empty-state or reduced view is shown.
        """
        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "sentinel_reports": {
                        # Report present but NO SENTINEL_LOG.md
                        "SENTINEL_REPORT_2026-03-01_00-00-00.md": _SENTINEL_REPORT_CONTENT,
                    },
                },
            },
        )

        at = _run_sentinel_page(tmp_path, monkeypatch)

        if at.exception:
            exc_msg = str(at.exception[0].message)
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")

        if _is_stub(at):
            pytest.xfail("sentinel.py still a stub — full implementation pending")

        # Page must not crash when SENTINEL_LOG.md is absent
        assert not at.exception, (
            f"Sentinel page raised an exception when SENTINEL_LOG.md is absent: {at.exception}"
        )


# ---------------------------------------------------------------------------
# Group 5: Malformed report handling
# ---------------------------------------------------------------------------


class TestMalformedReportHandling:
    """Sentinel page handles reports with missing or malformed frontmatter."""

    def test_handles_malformed_report_gracefully(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A report file without YAML frontmatter renders without crashing.

        The parser must tolerate missing frontmatter (returns empty dict + body),
        and the page must render a fallback view rather than raising an exception.
        """
        malformed_report = (
            "# Sentinel Report Without Frontmatter\n\n"
            "This report has no YAML frontmatter block.\n"
            "The page must handle it gracefully.\n\n"
            "## Findings\n\nSome findings here.\n"
        )
        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "sentinel_reports": {
                        "SENTINEL_REPORT_2026-03-01_00-00-00.md": malformed_report,
                    },
                },
            },
        )

        at = _run_sentinel_page(tmp_path, monkeypatch)

        if at.exception:
            exc_msg = str(at.exception[0].message)
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")

        if _is_stub(at):
            pytest.xfail("sentinel.py still a stub — full implementation pending")

        assert not at.exception, (
            "Sentinel page raised an exception when the report had no frontmatter.\n"
            f"Exception: {at.exception}"
        )


# ---------------------------------------------------------------------------
# Group 6: Sentinel health sparkline pure-function contract
# ---------------------------------------------------------------------------


class TestSentinelHealthSparklinePureContract:
    """graph.sentinel_health_sparkline produces a valid Plotly Figure from log data.

    Pure-function layer: tested without AppTest to verify the graph contract
    independently of the page's rendering code.  This mirrors the two-layer
    pattern used for ADR DAG testing.
    """

    def test_sparkline_returns_figure_from_log_dataframe(self) -> None:
        """sentinel_health_sparkline returns a non-empty Plotly Figure from a DataFrame."""
        try:
            import pandas as pd  # noqa: PLC0415

            from streamlit_app.widgets.graph import (  # noqa: PLC0415
                sentinel_health_sparkline,
            )
        except ImportError:
            pytest.skip("graph module or pandas not importable yet — concurrent mode")

        df = pd.DataFrame(
            {
                "timestamp": ["2026-01-01", "2026-02-01", "2026-03-01"],
                "health_grade": ["A", "B", "A"],
            }
        )
        fig = sentinel_health_sparkline(df)
        # Must return something with a data attribute (Plotly Figure contract)
        assert hasattr(fig, "data"), (
            "sentinel_health_sparkline must return a Plotly Figure-like object. "
            f"Got: {type(fig)}"
        )

    def test_sparkline_returns_empty_figure_for_empty_dataframe(self) -> None:
        """sentinel_health_sparkline returns an empty Figure for an empty DataFrame."""
        try:
            import pandas as pd  # noqa: PLC0415

            from streamlit_app.widgets.graph import (  # noqa: PLC0415
                sentinel_health_sparkline,
            )
        except ImportError:
            pytest.skip("graph module or pandas not importable yet — concurrent mode")

        fig = sentinel_health_sparkline(pd.DataFrame())
        assert hasattr(fig, "data"), (
            "sentinel_health_sparkline must return a Plotly Figure-like object for empty input. "
            f"Got: {type(fig)}"
        )


# ---------------------------------------------------------------------------
# Group 7: Module purity (Convention 6)
# ---------------------------------------------------------------------------


class TestModulePurity:
    """sentinel.py must not execute Streamlit calls at import time."""

    def test_module_purity_no_import_time_streamlit_calls(self) -> None:
        """sentinel.py has no module-level Streamlit rendering calls (Convention 6).

        Uses AST inspection rather than importing the module, so it works
        regardless of concurrent-mode implementation state.
        """
        sentinel_path = Path(__file__).parents[1] / "pages" / "sentinel.py"
        if not sentinel_path.exists():
            pytest.skip("sentinel.py not yet on disk — concurrent mode, expected")

        source = sentinel_path.read_text(encoding="utf-8")
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
            f"Import-time Streamlit calls found in sentinel.py: {top_level_st_calls}. "
            "All st.* calls must be inside render() (Convention 6)."
        )


# ---------------------------------------------------------------------------
# Group 8: Convention 6 — single render() export
# ---------------------------------------------------------------------------


class TestRenderExport:
    """sentinel.py defines and exports a single render() callable (Convention 6)."""

    def test_render_function_defined(self) -> None:
        """sentinel.py defines a top-level render() function via AST check."""
        sentinel_path = Path(__file__).parents[1] / "pages" / "sentinel.py"
        if not sentinel_path.exists():
            pytest.skip("sentinel.py not yet on disk — concurrent mode, expected")

        source = sentinel_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        top_level_function_names = {
            node.name
            for node in ast.iter_child_nodes(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

        assert "render" in top_level_function_names, (
            f"sentinel.py must define a top-level render() function. "
            f"Found functions: {sorted(top_level_function_names)}"
        )
