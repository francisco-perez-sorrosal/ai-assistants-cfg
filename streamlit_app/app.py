"""
Praxion Pipeline Dashboard — Streamlit entrypoint.

This is the ONLY file that calls st.set_page_config.  All page modules must
import streamlit after this module has already set page configuration, so they
must never call st.set_page_config themselves.

Environment variables consumed (via config.py)
----------------------------------------------
  PRAXION_PROJECT_ROOT           — required; absolute path to the target project.
  PRAXION_DASHBOARD_POLL_SECONDS — optional; default 15.

Usage
-----
  PRAXION_PROJECT_ROOT=/path/to/project streamlit run streamlit_app/app.py

Do NOT import from this module in tests — test individual page modules directly
by calling their render() functions.
"""

from __future__ import annotations

import importlib
from datetime import datetime

import streamlit as st

from streamlit_app.config import get_config

# ── Page registry ──────────────────────────────────────────────────────────────
# Order matches the SYSTEMS_PLAN component table row order:
# Architecture, Workshops, ADRs, Sentinel, Roadmap, Metrics.

_PAGE_SPECS = [
    {
        "module": "streamlit_app.pages.architecture",
        "title": "Architecture",
        "icon": "🏛️",
        "url_path": "architecture",
    },
    {
        "module": "streamlit_app.pages.workshops",
        "title": "Workshops",
        "icon": "🔧",
        "url_path": "workshops",
    },
    {
        "module": "streamlit_app.pages.adrs",
        "title": "ADRs",
        "icon": "📋",
        "url_path": "adrs",
    },
    {
        "module": "streamlit_app.pages.sentinel",
        "title": "Sentinel",
        "icon": "🛡️",
        "url_path": "sentinel",
    },
    {
        "module": "streamlit_app.pages.roadmap",
        "title": "Roadmap",
        "icon": "🗺️",
        "url_path": "roadmap",
    },
    {
        "module": "streamlit_app.pages.metrics",
        "title": "Metrics",
        "icon": "📊",
        "url_path": "metrics",
    },
    {
        "module": "streamlit_app.pages.documentation",
        "title": "Documentation",
        "icon": "📚",
        "url_path": "documentation",
    },
]

# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_page(spec: dict[str, str]) -> st.Page:
    """Build a st.Page entry for a page spec.

    Wraps the page module's render() in a safe error boundary so a data-layer
    exception on one page does not crash the entire navigation.
    """
    module_name = spec["module"]

    def _page_callable() -> None:
        _safe_page(module_name, spec["title"])

    return st.Page(
        _page_callable,
        title=spec["title"],
        icon=spec["icon"],
        url_path=spec["url_path"],
    )


def _safe_page(module_name: str, title: str) -> None:
    """Call a page module's render() with a graceful error boundary.

    Any exception raised by the page is caught and displayed as an error
    widget rather than crashing Streamlit's re-run loop.  This protects the
    navigation shell from transient data-layer failures.
    """
    try:
        mod = importlib.import_module(module_name)
        mod.render()
    except Exception as exc:
        st.error(
            f"**{title}** encountered an error while loading its data.\n\n"
            f"```\n{type(exc).__name__}: {exc}\n```\n\n"
            "This page will retry on the next refresh.  If the error persists, "
            "check that `PRAXION_PROJECT_ROOT` points to a valid Praxion project."
        )


def _render_sidebar(cfg: object) -> None:
    """Render the persistent sidebar header with project info."""
    with st.sidebar:
        st.title("🧭 Praxion Dashboard")
        st.markdown(f"**Project:** `{cfg.project_name}`")  # type: ignore[attr-defined]
        st.markdown(f"**Root:** `{cfg.project_root}`")  # type: ignore[attr-defined]
        st.markdown(
            f"**Refresh:** {cfg.poll_interval_seconds}s "  # type: ignore[attr-defined]
            f"(`PRAXION_DASHBOARD_POLL_SECONDS`)"
        )
        st.caption(f"Last loaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.divider()
        st.caption(f"Dashboard v{cfg.dashboard_version}")  # type: ignore[attr-defined]


# ── Entry point ────────────────────────────────────────────────────────────────


def main() -> None:
    """Configure the Streamlit application and run the selected page."""
    cfg = get_config()

    st.set_page_config(
        page_title=f"Praxion — {cfg.project_name}",
        page_icon="🧭",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _render_sidebar(cfg)

    pages_list = [_make_page(spec) for spec in _PAGE_SPECS]
    page = st.navigation(pages_list)
    page.run()


if __name__ == "__main__":
    main()
