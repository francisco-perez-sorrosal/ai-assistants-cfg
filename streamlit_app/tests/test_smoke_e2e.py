"""End-to-end smoke tests for the Praxion Pipeline Dashboard.

Two tests:

  test_app_imports_cleanly
      Import streamlit_app.app without raising an exception.  Catches any
      top-level side-effect or missing dependency that would break the app
      before it ever runs.

  test_all_six_pages_render_without_crash
      Build a fixture project root containing a minimal sample of every
      artifact family the dashboard reads, then run each of the six page
      modules via AppTest.from_string.  A page "passes" when its AppTest
      run completes with no exceptions raised (at.exception is falsy).

Navigation router coverage
--------------------------
The six page modules are exercised in the order defined in app.py's
_PAGE_SPECS: architecture, workshops, adrs, sentinel, roadmap, metrics.
Each module's render() is called inside an isolated AppTest script so that
a failure in one page does not cascade to others.

Fixture design
--------------
Uses the project_root fixture from conftest.py (tmp_path-scoped) together
with monkeypatch to inject PRAXION_PROJECT_ROOT.  get_config.cache_clear()
is called before each page run so the lru_cache reads the injected env var.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

# The six page module paths in navigation order (matches _PAGE_SPECS in app.py).
_PAGE_MODULES = [
    "streamlit_app.pages.architecture",
    "streamlit_app.pages.workshops",
    "streamlit_app.pages.adrs",
    "streamlit_app.pages.sentinel",
    "streamlit_app.pages.roadmap",
    "streamlit_app.pages.metrics",
]


def _page_script(module_name: str, project_root: Path) -> str:
    """Build an AppTest inline script for a single page module.

    The script sets PRAXION_PROJECT_ROOT, clears the config cache, and
    calls the module's render() function — matching the pattern established
    by the per-page test suites.
    """
    return (
        "import os\n"
        f"os.environ['PRAXION_PROJECT_ROOT'] = {str(project_root)!r}\n"
        "from streamlit_app.config import get_config; get_config.cache_clear()\n"
        f"from {module_name} import render\n"
        "render()\n"
    )


class TestAppImports:
    """Structural tests that do not require a running Streamlit instance."""

    def test_app_imports_cleanly(self) -> None:
        """Import streamlit_app.app without raising an exception.

        Validates that top-level module code (imports, module-level
        constants) is free of side effects and missing dependencies.
        """
        mod = importlib.import_module("streamlit_app.app")
        assert hasattr(mod, "main"), "app.main must be defined"
        assert callable(mod.main), "app.main must be callable"

    def test_page_registry_lists_expected_pages(self) -> None:
        """The _PAGE_SPECS registry must contain the expected page modules.

        Asserting against the named module list (rather than a count) makes
        the test stable against future additions while still catching
        accidental removal of an existing page.
        """
        from streamlit_app.app import _PAGE_SPECS  # noqa: PLC0415

        expected = {
            "streamlit_app.pages.architecture",
            "streamlit_app.pages.workshops",
            "streamlit_app.pages.adrs",
            "streamlit_app.pages.sentinel",
            "streamlit_app.pages.roadmap",
            "streamlit_app.pages.metrics",
            "streamlit_app.pages.documentation",
        }
        actual = {s["module"] for s in _PAGE_SPECS}
        missing = expected - actual
        assert not missing, f"Missing expected page modules: {missing}"

    def test_all_page_modules_importable(self) -> None:
        """Every module listed in _PAGE_SPECS must be importable."""
        from streamlit_app.app import _PAGE_SPECS  # noqa: PLC0415

        for spec in _PAGE_SPECS:
            mod = importlib.import_module(spec["module"])
            assert hasattr(mod, "render"), f"{spec['module']} must export render()"


class TestAllSixPagesRenderWithoutCrash:
    """End-to-end render tests covering all six dashboard pages."""

    def test_all_six_pages_render_without_crash(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Load fixture project, run each page, assert no exceptions raised.

        Uses the project_root fixture from conftest.py which contains a
        minimal sample of every artifact family (ARCHITECTURE.md, ADR
        drafts, sentinel report + log, metrics report json + log, idea
        ledger, .ai-work/sample-pipeline/ with WIP/PROGRESS, ROADMAP.md).

        Each page is exercised in a separate AppTest invocation so a crash
        on one page does not prevent the remaining pages from running.
        """
        monkeypatch.setenv("PRAXION_PROJECT_ROOT", str(project_root))
        failures: list[tuple[str, str]] = []

        for module_name in _PAGE_MODULES:
            script = _page_script(module_name, project_root)
            try:
                at = AppTest.from_string(script).run(timeout=10)
                if at.exception:
                    failures.append(
                        (module_name, f"{type(at.exception).__name__}: {at.exception}")
                    )
            except Exception as exc:  # noqa: BLE001
                failures.append(
                    (module_name, f"AppTest raised: {type(exc).__name__}: {exc}")
                )

        if failures:
            failure_lines = "\n".join(f"  {mod}: {err}" for mod, err in failures)
            pytest.fail(
                f"{len(failures)} of {len(_PAGE_MODULES)} pages raised exceptions:\n"
                f"{failure_lines}"
            )

    def test_architecture_page_renders_without_crash(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Architecture page renders without exception given fixture project."""
        monkeypatch.setenv("PRAXION_PROJECT_ROOT", str(project_root))
        script = _page_script("streamlit_app.pages.architecture", project_root)
        at = AppTest.from_string(script).run(timeout=10)
        assert not at.exception, f"architecture page crashed: {at.exception}"

    def test_workshops_page_renders_without_crash(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Workshops page renders without exception given fixture project."""
        monkeypatch.setenv("PRAXION_PROJECT_ROOT", str(project_root))
        script = _page_script("streamlit_app.pages.workshops", project_root)
        at = AppTest.from_string(script).run(timeout=10)
        assert not at.exception, f"workshops page crashed: {at.exception}"

    def test_adrs_page_renders_without_crash(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ADRs page renders without exception given fixture project."""
        monkeypatch.setenv("PRAXION_PROJECT_ROOT", str(project_root))
        script = _page_script("streamlit_app.pages.adrs", project_root)
        at = AppTest.from_string(script).run(timeout=10)
        assert not at.exception, f"adrs page crashed: {at.exception}"

    def test_sentinel_page_renders_without_crash(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sentinel page renders without exception given fixture project."""
        monkeypatch.setenv("PRAXION_PROJECT_ROOT", str(project_root))
        script = _page_script("streamlit_app.pages.sentinel", project_root)
        at = AppTest.from_string(script).run(timeout=10)
        assert not at.exception, f"sentinel page crashed: {at.exception}"

    def test_roadmap_page_renders_without_crash(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Roadmap page renders without exception given fixture project."""
        monkeypatch.setenv("PRAXION_PROJECT_ROOT", str(project_root))
        script = _page_script("streamlit_app.pages.roadmap", project_root)
        at = AppTest.from_string(script).run(timeout=10)
        assert not at.exception, f"roadmap page crashed: {at.exception}"

    def test_metrics_page_renders_without_crash(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Metrics page renders without exception given fixture project."""
        monkeypatch.setenv("PRAXION_PROJECT_ROOT", str(project_root))
        script = _page_script("streamlit_app.pages.metrics", project_root)
        at = AppTest.from_string(script).run(timeout=10)
        assert not at.exception, f"metrics page crashed: {at.exception}"
