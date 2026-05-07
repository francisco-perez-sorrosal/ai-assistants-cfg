"""Sentinel health page — ecosystem quality grades and tiered findings."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from streamlit_app.config import get_config
from streamlit_app.data import cache, discovery
from streamlit_app.widgets import artifact_card, empty_state
from streamlit_app.widgets import graph as graphw

# Path to the sentinel agent file relative to a Praxion project root.
_SENTINEL_AGENT_REL = "agents/sentinel.md"

# Ordered section headings to look for in the latest report body.
_FINDING_SECTIONS = ["Critical", "Important", "Suggested"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _render_log_sparkline(log_path: Path) -> None:
    """Render a health-grade sparkline from SENTINEL_LOG.md."""
    df = cache.cached_parse_sentinel_log(str(log_path), cache.mtime_of(log_path))
    if df.empty:
        return
    fig = graphw.sentinel_health_sparkline(df)
    st.plotly_chart(fig, use_container_width=True)


def _render_scorecard(report_path: Path, producer_path: str) -> None:
    """Render the latest sentinel report as a scorecard artifact_card."""
    fm, body = cache.cached_parse_frontmatter(
        str(report_path), cache.mtime_of(report_path)
    )
    title = report_path.stem.replace("_", " ")
    artifact_card.artifact_card(
        title=title,
        body_md=body,
        what_is_this=producer_path,
        metadata=fm if fm else None,
        expanded=False,
    )


def _render_findings(report_path: Path, producer_path: str) -> None:
    """Render Critical / Important / Suggested sections from the latest report."""
    sections = cache.cached_parse_md_sections(
        str(report_path), cache.mtime_of(report_path)
    )
    for heading in _FINDING_SECTIONS:
        section_body = sections.get(heading)
        if section_body is None:
            continue
        artifact_card.artifact_card(
            title=heading,
            body_md=section_body,
            what_is_this=producer_path,
            expanded=(heading == "Critical"),
        )


# ---------------------------------------------------------------------------
# Page entry point
# ---------------------------------------------------------------------------


def render() -> None:
    """Render the Sentinel health page."""
    config = get_config()
    reports = discovery.list_sentinel_reports(config.project_root)
    log_path = discovery.find_sentinel_log(config.project_root)
    producer_path = str(config.project_root / _SENTINEL_AGENT_REL)

    st.title("Sentinel Health")
    st.caption(
        "Ecosystem quality grades, historical sparkline, and tiered findings"
        " from the sentinel agent."
    )

    if not reports:
        empty_state.empty_state(
            artifact_name="Sentinel reports",
            producer_path=producer_path,
            explanation=(
                "No sentinel reports found. Run `/sentinel` from Claude Code"
                " to generate your first ecosystem health report."
            ),
        )
        return

    if log_path is not None:
        st.subheader("Health Grade History")
        _render_log_sparkline(log_path)

    latest = reports[0]
    st.subheader("Latest Report")
    _render_scorecard(latest, producer_path)

    st.subheader("Findings")
    _render_findings(latest, producer_path)
