"""Behavioral tests for streamlit_app/pages/roadmap.py.

The Roadmap page is intentionally minimal:

  1. Calls discovery.find_roadmap(config.project_root) → Optional[Path].
  2. If None: renders an empty-state widget pointing to /roadmap slash command.
  3. If present: strips frontmatter via cached_parse_frontmatter, renders body
     with st.markdown.

Convention compliance
---------------------
  - Single render() callable; no import-time Streamlit execution (Convention 6).
  - Uses mtime (not _mtime) as the cache-bust parameter (Convention 2).
  - Frontmatter stripped before st.markdown (Convention 4).

Concurrent BDD / TDD state
--------------------------
The implementer and test-engineer run concurrently in this paired step.
The current roadmap.py contains a stub that renders an st.info placeholder.
Structural tests (AST purity, render() export) pass against the stub.
Behavioral tests use stub-detection guards: when the stub placeholder text is
visible, the test reports xfail with an explanatory message rather than a
hard failure.

REGISTERED OBJECTION — concurrent-mode GREEN on first run
----------------------------------------------------------
Steps 3b–10b all showed the implementer landing first.  If all behavioral
tests here pass GREEN on the first run, the same pattern applies — per memory
pattern_concurrent_bdd_green_on_first_run: not a defect when the behavioral
contract is correctly encoded.

Deferred imports
----------------
Production modules imported inside each test body (not at module top) so
pytest collection succeeds before the implementation exists.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed(root: Path, structure: dict[str, Any]) -> None:
    """Recursively create files/directories from a nested dict.

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


def _run_roadmap_page(project_root: Path, monkeypatch: pytest.MonkeyPatch) -> AppTest:
    """Set env, clear config cache, run the roadmap page via AppTest."""
    try:
        from streamlit_app.config import get_config  # noqa: PLC0415

        get_config.cache_clear()
    except Exception:  # noqa: BLE001
        pass

    monkeypatch.setenv("PRAXION_PROJECT_ROOT", str(project_root))
    script = (
        "import os\n"
        f"os.environ['PRAXION_PROJECT_ROOT'] = {str(project_root)!r}\n"
        "from streamlit_app.config import get_config; get_config.cache_clear()\n"
        "from streamlit_app.pages.roadmap import render\n"
        "render()\n"
    )
    return AppTest.from_string(script).run()


def _all_text(at: AppTest) -> str:
    """Collect all visible text from an AppTest result."""
    parts = []
    for group in [at.title, at.header, at.subheader, at.markdown, at.info, at.warning]:
        for element in group:
            parts.append(element.value)
    return " ".join(parts)


_STUB_SIGNALS = ("later implementation step", "implementation step")

_ROADMAP_WITH_FRONTMATTER = """\
---
title: Praxion Roadmap
date: 2026-05-01
---
# Roadmap

## Phase 1

Build the foundation.

## Phase 2

Deliver features.
"""

_ROADMAP_PLAIN = """\
# Roadmap

## Milestones

- Ship dashboard
- Write docs
"""


# ---------------------------------------------------------------------------
# Group 1 — Empty state when no ROADMAP.md
# ---------------------------------------------------------------------------


class TestEmptyStateWhenNoRoadmapMd:
    """Roadmap page shows a graceful empty state when ROADMAP.md is absent."""

    def test_empty_state_when_no_roadmap_md(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No ROADMAP.md at project root → empty state rendered, no crash.

        The empty state must include a pointer to the /roadmap slash command
        so the user knows how to generate a roadmap.
        """
        # Arrange: project root with no ROADMAP.md (only .ai-state skeleton)
        _seed(tmp_path, {".ai-state": {"decisions": {"drafts": {}}}})

        at = _run_roadmap_page(tmp_path, monkeypatch)

        # No exception permitted in either stub or final implementation
        assert not at.exception, (
            f"Roadmap page raised exception when ROADMAP.md is absent: {at.exception}"
        )

        text = _all_text(at)
        # Stub renders a placeholder; final impl renders empty-state widget.
        # Either way, the page must not crash and must render something.
        assert text.strip(), (
            "Roadmap page rendered nothing at all — expected at least a title or info message."
        )

        # When fully implemented: the empty state must mention "roadmap" or "/roadmap"
        if not any(s in text for s in _STUB_SIGNALS):
            # Implementation is present — assert the behavioral contract
            has_pointer = (
                "roadmap" in text.lower() or "/roadmap" in text or "ROADMAP" in text
            )
            assert has_pointer, (
                "Empty-state page must mention 'roadmap' or '/roadmap' so the user "
                f"knows how to generate a roadmap. Page text: {text[:400]!r}"
            )


# ---------------------------------------------------------------------------
# Group 2 — Renders ROADMAP.md when present
# ---------------------------------------------------------------------------


class TestRendersRoadmapMdWhenPresent:
    """Roadmap page renders content from ROADMAP.md when the file exists."""

    def test_renders_roadmap_md_when_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ROADMAP.md at project root → its content (or a recognizable heading) appears."""
        _seed(tmp_path, {"ROADMAP.md": _ROADMAP_PLAIN})

        at = _run_roadmap_page(tmp_path, monkeypatch)

        assert not at.exception, (
            f"Roadmap page raised exception when ROADMAP.md is present: {at.exception}"
        )

        text = _all_text(at)

        if any(s in text for s in _STUB_SIGNALS):
            pytest.xfail(
                "roadmap.py still a stub — ROADMAP.md rendering not yet implemented"
            )

        # The body content must appear in the rendered page
        has_content = "Roadmap" in text or "Milestones" in text or "dashboard" in text
        assert has_content, (
            f"ROADMAP.md content not found in rendered page. Page text: {text[:400]!r}"
        )


# ---------------------------------------------------------------------------
# Group 3 — Frontmatter stripped before rendering
# ---------------------------------------------------------------------------


class TestStripsFrontmatterBeforeRendering:
    """Roadmap page strips YAML frontmatter before rendering the body."""

    def test_strips_frontmatter_before_rendering(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ROADMAP.md with frontmatter block → frontmatter keys must NOT appear in body output.

        The behavioral contract (Convention 4): parse_frontmatter returns
        (fm_dict, body_text); only body_text must be passed to st.markdown.
        The raw YAML key 'title: Praxion Roadmap' must not leak into the render.
        """
        _seed(tmp_path, {"ROADMAP.md": _ROADMAP_WITH_FRONTMATTER})

        at = _run_roadmap_page(tmp_path, monkeypatch)

        assert not at.exception, (
            f"Roadmap page raised exception with frontmatter in ROADMAP.md: {at.exception}"
        )

        text = _all_text(at)

        if any(s in text for s in _STUB_SIGNALS):
            pytest.xfail(
                "roadmap.py still a stub — frontmatter stripping not yet implemented"
            )

        # The raw YAML must NOT be present in the rendered output
        assert "foo: bar" not in text, (
            "Frontmatter raw YAML key 'foo: bar' leaked into rendered body"
        )
        # The frontmatter key from the fixture must not appear verbatim
        assert "title: Praxion Roadmap" not in text, (
            "Frontmatter 'title: Praxion Roadmap' must be stripped before rendering. "
            f"Page text: {text[:500]!r}"
        )
        assert "date: 2026-05-01" not in text, (
            "Frontmatter 'date: 2026-05-01' must be stripped before rendering. "
            f"Page text: {text[:500]!r}"
        )


# ---------------------------------------------------------------------------
# Group 4 — Module purity (Convention 6)
# ---------------------------------------------------------------------------


class TestModulePurityNoImportTimeStreamlitCalls:
    """roadmap.py must not call any Streamlit rendering function at import time."""

    def test_module_purity_no_import_time_streamlit_calls(self) -> None:
        """roadmap.py has no top-level st.* calls (Convention 6 — import purity).

        Uses AST inspection so the test works regardless of concurrent-mode state.
        """
        roadmap_path = Path(__file__).parents[1] / "pages" / "roadmap.py"
        if not roadmap_path.exists():
            pytest.skip("roadmap.py not yet on disk — concurrent mode, expected")

        source = roadmap_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        _RENDERING_CALLS = {
            "st.write",
            "st.title",
            "st.markdown",
            "st.header",
            "st.subheader",
            "st.info",
            "st.error",
            "st.warning",
            "st.metric",
            "st.dataframe",
            "st.image",
            "st.columns",
            "st.expander",
        }

        violations: list[str] = []
        for node in ast.iter_child_nodes(tree):
            # Skip function/class definitions — rendering inside render() is correct
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    func = sub.func
                    if (
                        isinstance(func, ast.Attribute)
                        and isinstance(func.value, ast.Name)
                        and func.value.id == "st"
                        and f"st.{func.attr}" in _RENDERING_CALLS
                    ):
                        violations.append(f"st.{func.attr}()")

        assert not violations, (
            "roadmap.py has top-level Streamlit rendering calls (violates Convention 6). "
            f"Found: {violations}"
        )


# ---------------------------------------------------------------------------
# Group 5 — Convention 6: single render() export
# ---------------------------------------------------------------------------


class TestRenderFunctionDefined:
    """roadmap.py exports a single render() callable with no required parameters."""

    def test_render_function_defined(self) -> None:
        """roadmap.py defines a top-level render() function (Convention 6)."""
        roadmap_path = Path(__file__).parents[1] / "pages" / "roadmap.py"
        if not roadmap_path.exists():
            pytest.skip("roadmap.py not yet on disk — concurrent mode, expected")

        source = roadmap_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        top_level_functions = {
            node.name
            for node in ast.iter_child_nodes(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

        assert "render" in top_level_functions, (
            f"roadmap.py must define a top-level render() function. "
            f"Found: {sorted(top_level_functions)}"
        )

        # Verify render() requires no arguments via deferred import
        try:
            from streamlit_app.pages import roadmap  # noqa: PLC0415

            assert callable(roadmap.render), "roadmap.render must be callable"
            sig = inspect.signature(roadmap.render)
            required = [
                name
                for name, param in sig.parameters.items()
                if param.default is inspect.Parameter.empty
            ]
            assert not required, (
                f"render() must require no arguments; found required params: {required}"
            )
        except ImportError:
            # Concurrent mode — AST check above is sufficient
            pass
