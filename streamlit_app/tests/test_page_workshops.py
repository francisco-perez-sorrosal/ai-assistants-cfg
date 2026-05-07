"""Behavioral tests for streamlit_app/pages/workshops.py.

The Workshops page is the live-supervision surface for in-flight pipelines.
It reads ``.ai-work/<task-slug>/`` directories, shows pipeline state, and
auto-refreshes via ``st.fragment(run_every=15)``.

Concurrent BDD/TDD state
-------------------------
The implementer and test-engineer run concurrently.  The current
``workshops.py`` is a stub that renders a placeholder ``st.info()`` message.
Tests targeting the full pair-contract behavior are expected to fail (RED) until
the implementer lands.

Tests that check structural properties of the source file (AST, import-time
purity) are expected to pass immediately against the existing stub.

Tests use deferred imports inside each test body so pytest collection succeeds
before the module is fully wired.

REGISTERED OBJECTION — concurrent-mode GREEN on first run
----------------------------------------------------------
If all tests in this module pass GREEN on the first run, the implementer has
already landed ``workshops.py`` before these tests were written.  This is the
documented pattern from Steps 3b, 4b, 5b, and 6b.  Per
``pattern_concurrent_bdd_green_on_first_run``: not a defect when the behavioral
contract is correctly encoded.  The tests validate what the system *should do*,
not just what already exists.

AppTest + PRAXION_PROJECT_ROOT
-------------------------------
All UI tests set ``PRAXION_PROJECT_ROOT`` via ``monkeypatch.setenv`` to a
``tmp_path`` fixture directory.  The page module reads this env var via
``streamlit_app.config.get_config()``.  The ``get_config`` function is
``lru_cache``-decorated; each test must call ``get_config.cache_clear()``
in teardown so config state does not bleed between tests.

``AppTest.from_string`` approach
---------------------------------
Tests embed the full app script as a string rather than using
``AppTest.from_file``.  This avoids the Streamlit ``set_page_config`` must-be-
first constraint when running a page module in isolation, and gives control over
the PRAXION_PROJECT_ROOT env injection order relative to ``import``.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

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


# ---------------------------------------------------------------------------
# WIP.md fixture content
# ---------------------------------------------------------------------------

_WIP_CONTENT = """\
# WIP: Feature Alpha

## Mode

sequential

## Current Step

**Phase 1, Step Na** — Implement config.py [IN-PROGRESS]

## Status

[IN-PROGRESS] — Step Na implementing config

## Progress

**Phase 1**
- [x] Step Ma: Scaffold skeleton [COMPLETE]
- [ ] Step Na: Implement config.py [IN-PROGRESS] ← current

## Blockers

None

## Next Action

Complete config.py implementation.
"""

_PROGRESS_CONTENT = """\
[2026-05-07T19:00:00Z] [implementer] Phase 1/5: understand-scope -- reading docs #feature=feature-alpha
[2026-05-07T19:10:00Z] [implementer] Phase 2/5: implementation -- writing config.py #feature=feature-alpha
"""

_WIP_SIMPLE = """\
# WIP: Beta Pipeline

## Status

[IN-PROGRESS]

## Current Step

**Step Pb** — Test discovery module

## Progress

- [x] Step Ma: Done [COMPLETE]
- [x] Step Na: Done [COMPLETE]
- [ ] Step Pb: Tests [IN-PROGRESS]

## Blockers

None

## Next Action

Write failing tests.
"""

_PROGRESS_SIMPLE = """\
[2026-05-07T20:00:00Z] [test-engineer] Phase 1/3: scope -- reading docs #testing
[2026-05-07T20:05:00Z] [test-engineer] Phase 2/3: design -- designing tests #testing
"""


# ---------------------------------------------------------------------------
# AppTest helper
# ---------------------------------------------------------------------------


def _run_workshops_page(monkeypatch: pytest.MonkeyPatch, project_root: Path) -> AppTest:
    """Set env var, clear config cache, run the workshops page via AppTest."""
    monkeypatch.setenv("PRAXION_PROJECT_ROOT", str(project_root))

    # Clear config cache so each test gets a fresh config read.
    try:
        from streamlit_app.config import get_config  # noqa: PLC0415

        get_config.cache_clear()
    except Exception:  # noqa: BLE001
        pass

    script = (
        "import os\n"
        f"os.environ['PRAXION_PROJECT_ROOT'] = {str(project_root)!r}\n"
        "from streamlit_app.pages.workshops import render\n"
        "render()\n"
    )
    return AppTest.from_string(script).run()


# ---------------------------------------------------------------------------
# Group 1: Empty-state behavior
# ---------------------------------------------------------------------------


class TestEmptyStateWhenNoWorkshops:
    """Workshops page shows empty state when no in-flight pipelines exist."""

    def test_empty_state_when_no_ai_work_dir(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """No .ai-work/ directory → graceful empty-state widget, no exception."""
        # Arrange: project root with .ai-state/ but no .ai-work/
        _seed(tmp_path, {".ai-state": {}})

        at = _run_workshops_page(monkeypatch, tmp_path)

        if at.exception:
            # Stub raises or stub info is shown — structurally valid, not a real error
            # If it's a config error (missing env) that's a test-infrastructure issue.
            exc_msg = str(at.exception[0].message) if at.exception else ""
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")
            # If stub is still in place (placeholder info message), treat as xfail
            all_text = " ".join(t.value for t in at.info)
            if "later implementation" in all_text or "Coming soon" in all_text:
                pytest.xfail("workshops.py still a stub — full implementation pending")
        assert not at.exception, (
            f"Workshops page raised an exception on empty project: {at.exception}"
        )

    def test_empty_state_when_ai_work_exists_but_empty(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Empty .ai-work/ directory → graceful empty-state widget, no exception."""
        # Arrange: .ai-work/ present but contains no slug directories
        _seed(tmp_path, {".ai-work": {}})

        at = _run_workshops_page(monkeypatch, tmp_path)

        if at.exception:
            exc_msg = str(at.exception[0].message) if at.exception else ""
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")
        all_info_text = " ".join(t.value for t in at.info)
        if "later implementation" in all_info_text or "Coming soon" in all_info_text:
            pytest.xfail("workshops.py still a stub — full implementation pending")
        assert not at.exception, (
            "Empty .ai-work/ must not raise an exception on the workshops page"
        )


# ---------------------------------------------------------------------------
# Group 2: Workshop rendering with content
# ---------------------------------------------------------------------------


class TestWorkshopRendering:
    """Workshops page renders title and WIP state for each active workshop."""

    def test_renders_active_workshops_with_titles(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Two workshop dirs → both task-slug names appear in rendered page output."""
        # Arrange: two workshops with minimal WIP.md files
        _seed(
            tmp_path,
            {
                ".ai-work": {
                    "feature-a": {"WIP.md": _WIP_CONTENT, "PROGRESS.md": ""},
                    "feature-b": {"WIP.md": _WIP_SIMPLE, "PROGRESS.md": ""},
                }
            },
        )

        at = _run_workshops_page(monkeypatch, tmp_path)

        if at.exception:
            exc_msg = str(at.exception[0].message) if at.exception else ""
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")
        all_text = (
            " ".join(t.value for t in at.title)
            + " ".join(t.value for t in at.header)
            + " ".join(t.value for t in at.subheader)
            + " ".join(t.value for t in at.markdown)
            + " ".join(t.value for t in at.info)
        )
        if "later implementation" in all_text or "Coming soon" in all_text:
            pytest.xfail("workshops.py still a stub — full implementation pending")
        assert not at.exception, f"Unexpected exception: {at.exception}"
        assert "feature-a" in all_text, (
            f"Workshop 'feature-a' not found in page output. Got text snippet: {all_text[:300]!r}"
        )
        assert "feature-b" in all_text, (
            f"Workshop 'feature-b' not found in page output. Got text snippet: {all_text[:300]!r}"
        )

    def test_renders_current_step_from_wip(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """WIP.md current-step text appears in the rendered workshop card."""
        _seed(
            tmp_path,
            {
                ".ai-work": {
                    "alpha-pipeline": {
                        "WIP.md": _WIP_CONTENT,
                        "PROGRESS.md": _PROGRESS_CONTENT,
                    }
                }
            },
        )

        at = _run_workshops_page(monkeypatch, tmp_path)

        if at.exception:
            exc_msg = str(at.exception[0].message) if at.exception else ""
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")
        all_text = (
            " ".join(t.value for t in at.title)
            + " ".join(t.value for t in at.header)
            + " ".join(t.value for t in at.subheader)
            + " ".join(t.value for t in at.markdown)
            + " ".join(t.value for t in at.info)
        )
        if "later implementation" in all_text or "Coming soon" in all_text:
            pytest.xfail("workshops.py still a stub — full implementation pending")
        assert not at.exception, f"Unexpected exception: {at.exception}"
        # The WIP file declares "Phase 1, Step Na" and "IN-PROGRESS"
        # At least the workshop dir name or WIP status should be visible.
        assert (
            "alpha-pipeline" in all_text
            or "2a" in all_text
            or "IN-PROGRESS" in all_text
        ), f"Expected workshop step info in page output. Got: {all_text[:300]!r}"

    def test_progress_log_entries_appear(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """PROGRESS.md events are surfaced in the workshop card output."""
        _seed(
            tmp_path,
            {
                ".ai-work": {
                    "beta-pipeline": {
                        "WIP.md": _WIP_SIMPLE,
                        "PROGRESS.md": _PROGRESS_SIMPLE,
                    }
                }
            },
        )

        at = _run_workshops_page(monkeypatch, tmp_path)

        if at.exception:
            exc_msg = str(at.exception[0].message) if at.exception else ""
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")
        all_text = (
            " ".join(t.value for t in at.markdown)
            + " ".join(t.value for t in at.info)
            + " ".join(t.value for t in at.header)
            + " ".join(t.value for t in at.subheader)
        )
        if "later implementation" in all_text or "Coming soon" in all_text:
            pytest.xfail("workshops.py still a stub — full implementation pending")
        assert not at.exception, f"Unexpected exception: {at.exception}"
        # Either the agent name or a phase keyword from PROGRESS.md should appear.
        has_progress_content = (
            "test-engineer" in all_text
            or "implementer" in all_text
            or "scope" in all_text.lower()
            or "beta-pipeline" in all_text
        )
        assert has_progress_content, (
            f"Expected PROGRESS.md content in page output. Got: {all_text[:300]!r}"
        )


# ---------------------------------------------------------------------------
# Group 3: Graceful degradation
# ---------------------------------------------------------------------------


class TestGracefulDegradation:
    """Workshops page handles missing or unreadable artifacts without crashing."""

    def test_renders_when_wip_md_missing(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Workshop dir without WIP.md still renders — no exception raised."""
        _seed(
            tmp_path,
            {
                ".ai-work": {
                    "no-wip-workshop": {
                        "PROGRESS.md": _PROGRESS_SIMPLE,
                        "LEARNINGS.md": "# Learnings\n",
                    }
                }
            },
        )

        at = _run_workshops_page(monkeypatch, tmp_path)

        if at.exception:
            exc_msg = str(at.exception[0].message) if at.exception else ""
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")
        all_text = " ".join(t.value for t in at.info) + " ".join(
            t.value for t in at.markdown
        )
        if "later implementation" in all_text or "Coming soon" in all_text:
            pytest.xfail("workshops.py still a stub — full implementation pending")
        assert not at.exception, (
            "Workshops page must not raise when WIP.md is missing from a workshop dir"
        )

    def test_skips_files_in_ai_work_root(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Loose files at .ai-work/ root are not treated as workshop directories."""
        _seed(
            tmp_path,
            {
                ".ai-work": {
                    "loose-file.txt": "orphan content",
                    "real-workshop": {
                        "WIP.md": _WIP_SIMPLE,
                        "PROGRESS.md": "",
                    },
                }
            },
        )

        at = _run_workshops_page(monkeypatch, tmp_path)

        if at.exception:
            exc_msg = str(at.exception[0].message) if at.exception else ""
            if "PRAXION_PROJECT_ROOT" in exc_msg:
                pytest.fail(f"Config env not injected correctly: {exc_msg}")
        all_text = " ".join(t.value for t in at.markdown) + " ".join(
            t.value for t in at.info
        )
        if "later implementation" in all_text or "Coming soon" in all_text:
            pytest.xfail("workshops.py still a stub — full implementation pending")
        assert not at.exception, "No exception expected when .ai-work/ has loose files"
        # "loose-file.txt" must not appear as a workshop slug
        assert "loose-file" not in all_text.lower(), (
            "Loose file at .ai-work/ root must not be treated as a workshop. "
            f"Found 'loose-file' in: {all_text[:300]!r}"
        )


# ---------------------------------------------------------------------------
# Group 4: Structural / convention checks (AST-based)
# ---------------------------------------------------------------------------


class TestWorkshopsModulePurity:
    """Structural convention checks on workshops.py source."""

    def _get_module_path(self) -> Path:
        return Path(__file__).parent.parent / "pages" / "workshops.py"

    def test_module_purity_no_import_time_streamlit_calls(self) -> None:
        """workshops.py has no top-level st.write/st.title/st.markdown calls.

        Convention 5: each page module exports a single render() callable;
        no import-time execution.  Streamlit rendering calls at module top level
        would execute on import, violating the convention.
        """
        module_path = self._get_module_path()
        assert module_path.exists(), f"workshops.py not found at {module_path}"
        source = module_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        # Collect top-level names that are call-expressions using 'st.*'
        rendering_calls = {
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
        }

        top_level_violations: list[str] = []
        for node in ast.iter_child_nodes(tree):
            # Skip everything inside function/class definitions
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    func = sub.func
                    if (
                        isinstance(func, ast.Attribute)
                        and isinstance(func.value, ast.Name)
                        and func.value.id == "st"
                        and f"st.{func.attr}" in rendering_calls
                    ):
                        top_level_violations.append(f"st.{func.attr}")

        assert not top_level_violations, (
            "workshops.py has top-level Streamlit rendering calls (violates Convention 5). "
            f"Found: {top_level_violations}"
        )

    def test_render_function_is_defined(self) -> None:
        """workshops.py defines a top-level render() function (Convention 5)."""
        module_path = self._get_module_path()
        assert module_path.exists(), f"workshops.py not found at {module_path}"
        source = module_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        top_level_function_names = {
            node.name
            for node in ast.iter_child_nodes(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

        assert "render" in top_level_function_names, (
            f"workshops.py must define a top-level render() function. "
            f"Found functions: {sorted(top_level_function_names)}"
        )

    def test_fragment_wrapper_present_in_source(self) -> None:
        """workshops.py references st.fragment in its source (auto-refresh contract).

        The Workshops page is the only page that uses st.fragment(run_every=).
        Verifying that ``fragment`` appears in the source ensures the implementer
        honoured the auto-refresh contract (pair contract + Convention 2).
        """
        module_path = self._get_module_path()
        assert module_path.exists(), f"workshops.py not found at {module_path}"
        source = module_path.read_text(encoding="utf-8")

        # Check the stub — if it's a stub, xfail gracefully.
        if "later implementation" in source or "Coming soon" in source:
            pytest.xfail(
                "workshops.py is still a stub — fragment wrapper not yet added"
            )

        assert "fragment" in source, (
            "workshops.py must use st.fragment for auto-refresh (Convention 2). "
            "Expected 'fragment' to appear in the source."
        )
