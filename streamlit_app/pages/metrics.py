"""Metrics page — KPI grid + aggregate trends. Supersedes the static metrics viewer."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from streamlit_app.config import get_config
from streamlit_app.data import cache, discovery
from streamlit_app.widgets import empty_state
from streamlit_app.widgets import graph as graphw

# Path to the producer command relative to a Praxion project root.
_PRODUCER_REL = "scripts/project_metrics/"

# Number of KPI tiles per row in the grid.
_COLS_PER_ROW = 4


def render() -> None:
    """Render the Metrics page (KPI grid + historical trend chart)."""
    config = get_config()
    json_reports = discovery.list_metrics_reports_json(config.project_root)
    log_path = discovery.find_metrics_log(config.project_root)

    st.title("Metrics")
    st.caption(
        "KPI grid from the latest project-metrics run + historical trends"
        " from `METRICS_LOG.md`."
    )

    if not json_reports and log_path is None:
        empty_state.empty_state(
            artifact_name="Project metrics",
            producer_path=str(config.project_root / _PRODUCER_REL),
            explanation=(
                "No metrics yet. Run `/project-metrics` to generate the first report."
            ),
        )
        return

    # KPI grid — from the latest JSON report's aggregate block.
    if json_reports:
        latest = json_reports[0]
        _render_kpi_grid(latest)

    # Trend chart — from METRICS_LOG.md.
    if log_path is not None:
        _render_trend_chart(log_path)


def _render_kpi_grid(latest_json: Path) -> None:
    """Parse the latest JSON report and render aggregate scalars as metric tiles."""
    try:
        data = cache.cached_parse_metrics_report_json(
            str(latest_json), cache.mtime_of(latest_json)
        )
        agg = data.get("aggregate") or {}
        if not agg:
            return
        _render_metric_tiles(agg)
    except Exception as exc:
        st.error(f"Could not parse latest metrics report: {exc}")


def _render_metric_tiles(agg: dict) -> None:  # type: ignore[type-arg]
    """Render aggregate scalars as a grid of `st.metric` tiles.

    Iterates over every key in `agg`. Non-scalar values (lists, dicts) are
    skipped. Up to 60 tiles are rendered; remainder is silently dropped.
    """
    items = [
        (k, v)
        for k, v in agg.items()
        if isinstance(v, (int, float, str)) and v is not None
    ][:60]

    for row_start in range(0, len(items), _COLS_PER_ROW):
        row = items[row_start : row_start + _COLS_PER_ROW]
        cols = st.columns(len(row))
        for col, (key, value) in zip(cols, row):
            label = key.replace("_", " ").title()
            col.metric(label=label, value=value)


def _render_trend_chart(log_path: Path) -> None:
    """Parse METRICS_LOG.md and render the aggregate-lines trend chart."""
    try:
        df = cache.cached_parse_metrics_log(str(log_path), cache.mtime_of(log_path))
        if df.empty:
            return
        st.subheader("Aggregate Trends")
        fig = graphw.metrics_aggregate_lines(df)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as exc:
        st.error(f"Could not parse metrics log: {exc}")
