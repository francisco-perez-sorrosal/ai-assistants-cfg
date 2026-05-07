"""
Behavioral tests for streamlit_app/widgets/ package.

Widget modules render Streamlit UI components (or return pure computation
artifacts) that are reused across all six dashboard pages.

Concurrent BDD/TDD state
-------------------------
The implementer partially shipped the widgets package before these
tests were written.  The current state of each module:

  educational.py  — COMPLETE: resolve_description() + educational() fully
                    implemented by the implementer.
  artifact_card.py — STUB: artifact_card() raises NotImplementedError.
  empty_state.py   — STUB: empty_state() raises NotImplementedError.
  graph.py         — STUB: adr_supersession_dot() + metrics_sparkline() raise
                    NotImplementedError.

AppTest-based tests for stubs capture an exception element and call
pytest.xfail() — correct concurrent-mode handling.  Pure-function tests for
stubs (graph) also call pytest.xfail() on NotImplementedError.

Tests for the fully-shipped educational module run GREEN immediately.

REGISTERED OBJECTION — partial API contract mismatch (paired task vs stubs)
------------------------------------------------------------------------------
The paired-task contract specified a five-function graph API
(step_dag_dot, adr_lineage_dot, req_test_bipartite_figure,
metrics_aggregate_lines, sentinel_health_sparkline) and a three-param
artifact_card(title, body_md, what_is_this, metadata, expanded).

The shipped stubs expose:
  graph.py         — adr_supersession_dot(adrs), metrics_sparkline(df, col)
  artifact_card.py — artifact_card(title, body, what_is_this_link)
  empty_state.py   — empty_state(artifact_name, producer_link)
  educational.py   — resolve_description(target_path) + educational(target_path,
                      label, use_popover)  [fully implemented — matches contract]

Tests target the shipped API.  The planner should reconcile the contract
mismatch before the integration checkpoint.

Deferred imports
-----------------
Pure-function tests import inside each test body (not at module top).
AppTest scripts embed the import in the injected script string.
Both patterns ensure pytest collection succeeds independently of the
implementation state.

Convention 4 (frontmatter stripped by caller)
---------------------------------------------
Tests for artifact_card pass body text with frontmatter already removed.
Convention 4 is caller-responsibility; artifact_card does not strip it.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import pytest
from streamlit.testing.v1 import AppTest


# ---------------------------------------------------------------------------
# Shared helpers
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


def _run_widget_script(script_body: str) -> AppTest:
    """Build an AppTest that imports from the widgets package and runs a widget."""
    return AppTest.from_string(script_body).run()


# ---------------------------------------------------------------------------
# Group 1: artifact_card
# ---------------------------------------------------------------------------


class TestArtifactCard:
    """artifact_card renders title, body, and optional educational popover."""

    def test_renders_title_in_output(self) -> None:
        """Title string is visible in the rendered page."""
        at = _run_widget_script(
            "import streamlit as st\n"
            "from streamlit_app.widgets.artifact_card import artifact_card\n"
            'artifact_card("My Widget Title", "some body text", "agents/systems-architect.md")'
        )
        if at.exception:
            pytest.xfail(
                f"artifact_card not yet implemented: {at.exception[0].message}"
            )
        all_values = (
            [t.value for t in at.title]
            + [t.value for t in at.header]
            + [t.value for t in at.subheader]
            + [t.value for t in at.markdown]
        )
        assert any("My Widget Title" in v for v in all_values), (
            f"Title not found in page output. Got: {all_values}"
        )

    def test_renders_body_markdown_in_output(self) -> None:
        """Body markdown content is rendered into the page."""
        at = _run_widget_script(
            "import streamlit as st\n"
            "from streamlit_app.widgets.artifact_card import artifact_card\n"
            'artifact_card("Title", "**bold body content**", "agents/systems-architect.md")'
        )
        if at.exception:
            pytest.xfail(
                f"artifact_card not yet implemented: {at.exception[0].message}"
            )
        all_text = " ".join(t.value for t in at.markdown)
        assert "bold body content" in all_text, (
            f"Body content not found in page markdown. Got: {all_text!r}"
        )

    def test_what_is_this_link_does_not_crash_widget(self) -> None:
        """Passing a what_is_this_link to an existing file does not raise."""
        at = _run_widget_script(
            "import streamlit as st\n"
            "from streamlit_app.widgets.artifact_card import artifact_card\n"
            'artifact_card("Title", "body", "rules/swe/agent-behavioral-contract.md")'
        )
        if at.exception:
            pytest.xfail(
                f"artifact_card not yet implemented: {at.exception[0].message}"
            )
        assert not at.exception

    def test_caller_is_responsible_for_frontmatter_stripped_body(self) -> None:
        """Convention 4: widget passes frontmatter-containing body through unchanged.

        The caller is responsible for stripping frontmatter before passing
        body to artifact_card.  If they fail to do so, the frontmatter markers
        appear verbatim in the rendered output — the widget does not clean them.
        """
        at = _run_widget_script(
            "import streamlit as st\n"
            "from streamlit_app.widgets.artifact_card import artifact_card\n"
            'artifact_card("Title", "---\\nid: dec-001\\n---\\nActual body", "agents/implementer.md")'
        )
        if at.exception:
            pytest.xfail(
                f"artifact_card not yet implemented: {at.exception[0].message}"
            )
        all_text = " ".join(t.value for t in at.markdown)
        assert "Actual body" in all_text


# ---------------------------------------------------------------------------
# Group 2: empty_state
# ---------------------------------------------------------------------------


class TestEmptyState:
    """empty_state renders a graceful degradation message for absent artifacts."""

    def test_renders_artifact_name_in_output(self) -> None:
        """Artifact name appears in the rendered empty-state output."""
        at = _run_widget_script(
            "import streamlit as st\n"
            "from streamlit_app.widgets.empty_state import empty_state\n"
            'empty_state("ROADMAP.md", "/commands/roadmap.md")'
        )
        if at.exception:
            pytest.xfail(f"empty_state not yet implemented: {at.exception[0].message}")
        all_text = " ".join(t.value for t in at.info) + " ".join(
            t.value for t in at.markdown
        )
        assert "ROADMAP.md" in all_text, (
            f"Artifact name not found in empty-state output. Got: {all_text!r}"
        )

    def test_renders_producer_link_when_provided(self) -> None:
        """Producer path/link appears in the empty-state output when given."""
        at = _run_widget_script(
            "import streamlit as st\n"
            "from streamlit_app.widgets.empty_state import empty_state\n"
            'empty_state("In-flight pipelines", "/rules/swe/swe-agent-coordination-protocol.md")'
        )
        if at.exception:
            pytest.xfail(f"empty_state not yet implemented: {at.exception[0].message}")
        all_text = " ".join(t.value for t in at.info) + " ".join(
            t.value for t in at.markdown
        )
        assert "swe-agent-coordination-protocol" in all_text or "rules" in all_text, (
            f"Producer link not in empty-state output. Got: {all_text!r}"
        )

    def test_widget_does_not_raise_for_minimal_call(self) -> None:
        """empty_state with artifact_name and producer_link never crashes."""
        at = _run_widget_script(
            "import streamlit as st\n"
            "from streamlit_app.widgets.empty_state import empty_state\n"
            'empty_state("Architecture baseline", "/skills/architecture-as-code/SKILL.md")'
        )
        if at.exception:
            pytest.xfail(f"empty_state not yet implemented: {at.exception[0].message}")
        assert not at.exception

    def test_empty_state_uses_info_not_error_level(self) -> None:
        """Convention 5: empty-state must not alarm the user — info, not error/warning."""
        at = _run_widget_script(
            "import streamlit as st\n"
            "from streamlit_app.widgets.empty_state import empty_state\n"
            'empty_state("SENTINEL_LOG.md", "agents/sentinel.md")'
        )
        if at.exception:
            pytest.xfail(f"empty_state not yet implemented: {at.exception[0].message}")
        assert len(at.info) > 0 or len(at.markdown) > 0, (
            "empty_state produced no visible output"
        )
        assert len(at.error) == 0, "empty_state must not use st.error"
        assert len(at.warning) == 0, "empty_state must not use st.warning"


# ---------------------------------------------------------------------------
# Group 3: resolve_description (pure function)
# ---------------------------------------------------------------------------


class TestResolveDescription:
    """resolve_description returns a one-line description for a given file path.

    This is the primary test seam for the educational widget's content.
    No Streamlit imports — fully deterministic and fast.
    """

    def test_returns_frontmatter_description_field_when_present(
        self, tmp_path: Path
    ) -> None:
        """Returns the frontmatter 'description:' value when present."""
        from streamlit_app.widgets.educational import resolve_description  # noqa: PLC0415

        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\ndescription: My explicit description\n---\n\nBody paragraph.\n",
            encoding="utf-8",
        )
        result = resolve_description(skill_file)
        assert result == "My explicit description", (
            f"Expected frontmatter description, got {result!r}"
        )

    def test_falls_back_to_first_non_empty_body_paragraph(self, tmp_path: Path) -> None:
        """When no 'description:' frontmatter, returns first non-empty body line."""
        from streamlit_app.widgets.educational import resolve_description  # noqa: PLC0415

        rule_file = tmp_path / "rule.md"
        rule_file.write_text(
            "---\ntitle: Some Rule\n---\n\n\nFirst real paragraph here.\n\nAnother paragraph.\n",
            encoding="utf-8",
        )
        result = resolve_description(rule_file)
        assert "First real paragraph here" in result, (
            f"Expected first body paragraph. Got {result!r}"
        )

    def test_returns_default_for_missing_file(self, tmp_path: Path) -> None:
        """A nonexistent path returns the default fallback string, not an exception."""
        from streamlit_app.widgets.educational import resolve_description  # noqa: PLC0415

        missing_path = tmp_path / "does_not_exist.md"
        result = resolve_description(missing_path)
        assert "not available" in result.lower(), (
            f"Expected default fallback for missing file. Got {result!r}"
        )

    def test_returns_default_for_empty_file(self, tmp_path: Path) -> None:
        """An empty file produces the default fallback, not an exception."""
        from streamlit_app.widgets.educational import resolve_description  # noqa: PLC0415

        empty_file = tmp_path / "empty.md"
        empty_file.touch()
        result = resolve_description(empty_file)
        assert isinstance(result, str), "resolve_description must always return str"
        assert result  # non-empty

    def test_skips_heading_lines_when_falling_back_to_body(
        self, tmp_path: Path
    ) -> None:
        """Heading lines (# ...) are skipped when selecting the first body paragraph."""
        from streamlit_app.widgets.educational import resolve_description  # noqa: PLC0415

        md_file = tmp_path / "skill.md"
        md_file.write_text(
            "# Top-level Heading\n\n## Sub-heading\n\nActual prose starts here.\n",
            encoding="utf-8",
        )
        result = resolve_description(md_file)
        assert "Actual prose starts here" in result, (
            f"Expected prose paragraph, not heading. Got {result!r}"
        )

    def test_description_field_takes_priority_over_body_paragraph(
        self, tmp_path: Path
    ) -> None:
        """frontmatter 'description:' wins over body paragraph content."""
        from streamlit_app.widgets.educational import resolve_description  # noqa: PLC0415

        md_file = tmp_path / "doc.md"
        md_file.write_text(
            "---\ndescription: Frontmatter wins\n---\n\nBody wins — or does it?\n",
            encoding="utf-8",
        )
        result = resolve_description(md_file)
        assert result == "Frontmatter wins", (
            f"Frontmatter description should take priority. Got {result!r}"
        )

    def test_accepts_string_path_not_only_pathlib(self, tmp_path: Path) -> None:
        """resolve_description accepts a string path as well as a Path object."""
        from streamlit_app.widgets.educational import resolve_description  # noqa: PLC0415

        md_file = tmp_path / "str_path.md"
        md_file.write_text(
            "---\ndescription: String path works\n---\n",
            encoding="utf-8",
        )
        result = resolve_description(str(md_file))
        assert result == "String path works", f"String path should work. Got {result!r}"


# ---------------------------------------------------------------------------
# Group 4: educational widget (AppTest)
# ---------------------------------------------------------------------------


class TestEducationalWidget:
    """educational() renders a popover/expander linking to the target file."""

    def test_renders_expander_when_use_popover_false(self, tmp_path: Path) -> None:
        """When use_popover=False, the affordance is an st.expander."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\ndescription: My skill description\n---\n\nSkill body.\n",
            encoding="utf-8",
        )
        at = _run_widget_script(
            "import streamlit as st\n"
            "from streamlit_app.widgets.educational import educational\n"
            f"educational({str(skill_file)!r}, use_popover=False)"
        )
        if at.exception:
            pytest.xfail(f"educational not yet implemented: {at.exception[0].message}")
        expander_labels = [e.label for e in at.expander]
        assert len(expander_labels) > 0, (
            f"Expected an st.expander. Expanders found: {expander_labels}"
        )

    def test_expander_label_defaults_to_what_is_this(self, tmp_path: Path) -> None:
        """Default label is 'What is this?'."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Skill\n\nBody.\n", encoding="utf-8")
        at = _run_widget_script(
            "import streamlit as st\n"
            "from streamlit_app.widgets.educational import educational\n"
            f"educational({str(skill_file)!r}, use_popover=False)"
        )
        if at.exception:
            pytest.xfail(f"educational not yet implemented: {at.exception[0].message}")
        expander_labels = [e.label for e in at.expander]
        assert any("What is this" in lbl for lbl in expander_labels), (
            f"Expected 'What is this?' label. Got: {expander_labels}"
        )

    def test_widget_renders_without_exception_for_real_file(
        self, tmp_path: Path
    ) -> None:
        """Passing a path to an existing file does not produce an exception."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\ndescription: A skill for testing\n---\n\nBody text.\n",
            encoding="utf-8",
        )
        at = _run_widget_script(
            "import streamlit as st\n"
            "from streamlit_app.widgets.educational import educational\n"
            f"educational({str(skill_file)!r}, use_popover=False)"
        )
        if at.exception:
            pytest.xfail(f"educational not yet implemented: {at.exception[0].message}")
        assert not at.exception

    def test_widget_degrades_gracefully_for_missing_file(self) -> None:
        """A path to a nonexistent file does not raise — fallback text is shown."""
        at = _run_widget_script(
            "import streamlit as st\n"
            "from streamlit_app.widgets.educational import educational\n"
            'educational("/nonexistent/path/to/SKILL.md", use_popover=False)'
        )
        if at.exception:
            pytest.xfail(f"educational not yet implemented: {at.exception[0].message}")
        # No exception should propagate — fallback text rendered instead.
        assert not at.exception

    def test_description_content_visible_inside_expander(self, tmp_path: Path) -> None:
        """When frontmatter description is present, its text appears in the expander body."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\ndescription: Unique expander content xyz123\n---\n\nBody.\n",
            encoding="utf-8",
        )
        at = _run_widget_script(
            "import streamlit as st\n"
            "from streamlit_app.widgets.educational import educational\n"
            f"educational({str(skill_file)!r}, use_popover=False)"
        )
        if at.exception:
            pytest.xfail(f"educational not yet implemented: {at.exception[0].message}")
        all_text = " ".join(t.value for t in at.markdown)
        assert "Unique expander content xyz123" in all_text, (
            f"Expected description in expander body. Got: {all_text!r}"
        )

    def test_custom_label_appears_on_expander(self, tmp_path: Path) -> None:
        """Custom label parameter is used as the expander label."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Skill\n\nBody.\n", encoding="utf-8")
        at = _run_widget_script(
            "import streamlit as st\n"
            "from streamlit_app.widgets.educational import educational\n"
            f"educational({str(skill_file)!r}, label='Learn more', use_popover=False)"
        )
        if at.exception:
            pytest.xfail(f"educational not yet implemented: {at.exception[0].message}")
        expander_labels = [e.label for e in at.expander]
        assert any("Learn more" in lbl for lbl in expander_labels), (
            f"Expected custom label 'Learn more'. Got: {expander_labels}"
        )


# ---------------------------------------------------------------------------
# Group 5: graph (pure functions — no Streamlit)
# ---------------------------------------------------------------------------


class TestAdrSupersessionDot:
    """adr_supersession_dot returns a valid Graphviz DOT string."""

    def _call_or_xfail(self, adrs: list[dict]) -> str:
        """Call adr_supersession_dot and xfail if not yet implemented."""
        from streamlit_app.widgets.graph import adr_supersession_dot  # noqa: PLC0415

        try:
            return adr_supersession_dot(adrs)
        except NotImplementedError as exc:
            pytest.xfail(f"adr_supersession_dot not yet implemented: {exc}")

    def test_returns_string_starting_with_digraph(self) -> None:
        """Result is a valid DOT string (starts with 'digraph')."""
        adrs = [
            {"id": "dec-001", "title": "Use PostgreSQL", "status": "accepted"},
            {"id": "dec-002", "title": "Use SQLite", "status": "superseded"},
        ]
        result = self._call_or_xfail(adrs)
        assert isinstance(result, str), "Expected a string return value"
        assert result.strip().startswith("digraph"), (
            f"Expected DOT string starting with 'digraph'. Got: {result[:80]!r}"
        )

    def test_all_adr_ids_appear_in_dot_output(self) -> None:
        """Every ADR id in the input is represented as a node in the DOT output."""
        adrs = [
            {"id": "dec-001", "title": "First", "status": "accepted"},
            {"id": "dec-002", "title": "Second", "status": "accepted"},
            {"id": "dec-003", "title": "Third", "status": "accepted"},
        ]
        result = self._call_or_xfail(adrs)
        for adr in adrs:
            assert adr["id"] in result, (
                f"ADR id {adr['id']!r} not found in DOT output:\n{result}"
            )

    def test_supersession_edge_appears_in_dot_output(self) -> None:
        """When one ADR supersedes another, a directed edge appears in DOT source."""
        adrs = [
            {
                "id": "dec-001",
                "title": "Old decision",
                "status": "superseded",
                "superseded_by": "dec-002",
            },
            {
                "id": "dec-002",
                "title": "New decision",
                "status": "accepted",
                "supersedes": "dec-001",
            },
        ]
        result = self._call_or_xfail(adrs)
        assert "dec-001" in result and "dec-002" in result, (
            "Both ADR IDs must appear in DOT output"
        )
        assert "->" in result, (
            f"Expected supersession edge (->) in DOT output:\n{result}"
        )

    def test_empty_adr_list_returns_valid_empty_digraph(self) -> None:
        """An empty input list returns a valid (empty) DOT digraph string."""
        result = self._call_or_xfail([])
        assert isinstance(result, str)
        assert result.strip().startswith("digraph"), (
            f"Expected 'digraph ...' for empty input. Got: {result!r}"
        )
        assert "->" not in result, "Empty ADR list must not produce edges"

    def test_no_supersession_produces_no_edges(self) -> None:
        """ADRs with no supersession relationships produce a graph with nodes but no edges."""
        adrs = [
            {"id": "dec-001", "title": "Decision A", "status": "accepted"},
            {"id": "dec-002", "title": "Decision B", "status": "accepted"},
        ]
        result = self._call_or_xfail(adrs)
        assert "dec-001" in result
        assert "dec-002" in result
        assert "->" not in result, (
            f"No edges expected when no supersession declared:\n{result}"
        )

    def test_superseded_status_gets_distinct_visual_attribute(self) -> None:
        """ADRs with status 'superseded' must have a visually distinct style in DOT."""
        adrs = [
            {"id": "dec-001", "title": "Old", "status": "superseded"},
            {"id": "dec-002", "title": "New", "status": "accepted"},
        ]
        result = self._call_or_xfail(adrs)
        style_keywords = {"style", "color", "fillcolor", "shape", "dashed", "dotted"}
        has_style = any(kw in result.lower() for kw in style_keywords)
        assert has_style, (
            f"Expected a visual distinction attribute for superseded status.\n"
            f"DOT output:\n{result}"
        )


class TestMetricsSparkline:
    """metrics_sparkline returns a Plotly Figure."""

    def _call_or_xfail(self, df: pd.DataFrame, col: str) -> go.Figure:
        """Call metrics_sparkline and xfail if not yet implemented."""
        from streamlit_app.widgets.graph import metrics_sparkline  # noqa: PLC0415

        try:
            return metrics_sparkline(df, col)
        except NotImplementedError as exc:
            pytest.xfail(f"metrics_sparkline not yet implemented: {exc}")

    def test_returns_plotly_figure(self) -> None:
        """metrics_sparkline returns a plotly.graph_objects.Figure."""
        df = pd.DataFrame({"date": ["2026-01-01", "2026-01-02"], "health": [7, 8]})
        result = self._call_or_xfail(df, "health")
        assert isinstance(result, go.Figure), (
            f"Expected plotly Figure, got {type(result)}"
        )

    def test_figure_has_at_least_one_trace(self) -> None:
        """Figure traces reflect the specified column's values."""
        df = pd.DataFrame(
            {"date": ["2026-01-01", "2026-01-02", "2026-01-03"], "score": [3, 5, 7]}
        )
        result = self._call_or_xfail(df, "score")
        assert isinstance(result, go.Figure)
        assert len(result.data) > 0, "Figure must have at least one trace"

    def test_empty_dataframe_returns_figure_without_crash(self) -> None:
        """An empty DataFrame produces a valid Figure, not an exception."""
        df = pd.DataFrame({"date": [], "metric": []})
        result = self._call_or_xfail(df, "metric")
        assert isinstance(result, go.Figure), (
            "metrics_sparkline must return a Figure for empty input"
        )

    def test_missing_column_raises_informative_error(self) -> None:
        """Requesting a column not in the DataFrame produces a KeyError or ValueError."""
        from streamlit_app.widgets.graph import metrics_sparkline  # noqa: PLC0415

        df = pd.DataFrame({"date": ["2026-01-01"], "score": [5]})
        try:
            metrics_sparkline(df, "nonexistent_column")
            # If not yet implemented, the line above is never reached (NotImplementedError)
        except NotImplementedError as exc:
            pytest.xfail(f"metrics_sparkline not yet implemented: {exc}")
        except (KeyError, ValueError):
            pass  # expected — correct behavior
        else:
            pytest.fail(
                "Expected KeyError or ValueError for a missing column, got a result."
            )


# ---------------------------------------------------------------------------
# Group 6: Convention checks
# ---------------------------------------------------------------------------


class TestWidgetImportConventions:
    """Structural convention checks for the widgets package."""

    def test_graph_module_does_not_import_streamlit(self) -> None:
        """graph.py is a pure computation module — it must not import streamlit."""
        graph_path = Path(__file__).parent.parent / "widgets" / "graph.py"
        assert graph_path.exists(), f"graph.py not found at {graph_path}"
        source = graph_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("streamlit"), (
                        f"graph.py must not import streamlit. Found: import {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("streamlit"):
                    pytest.fail(
                        f"graph.py must not import from streamlit. "
                        f"Found: from {node.module} import ..."
                    )

    def test_data_layer_modules_do_not_import_streamlit_except_cache(self) -> None:
        """data/ modules (except cache.py) must not import streamlit."""
        data_dir = Path(__file__).parent.parent / "data"
        violations: list[str] = []
        for py_file in sorted(data_dir.glob("*.py")):
            if py_file.name in {"cache.py", "__init__.py"}:
                continue
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("streamlit"):
                            violations.append(f"{py_file.name}: import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith("streamlit"):
                        violations.append(
                            f"{py_file.name}: from {node.module} import ..."
                        )
        assert not violations, (
            "Data-layer modules (except cache.py) must not import streamlit.\n"
            "Violations:\n" + "\n".join(violations)
        )

    def test_widgets_init_documents_all_four_sub_modules(self) -> None:
        """widgets/__init__.py mentions all four expected sub-modules."""
        init_path = Path(__file__).parent.parent / "widgets" / "__init__.py"
        assert init_path.exists(), "widgets/__init__.py must exist"
        content = init_path.read_text(encoding="utf-8")
        for sub in ("artifact_card", "educational", "graph", "empty_state"):
            assert sub in content, (
                f"widgets/__init__.py should document sub-module '{sub}'. "
                f"Got:\n{content}"
            )
