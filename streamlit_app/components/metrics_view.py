"""Metrics-view renderer — aggregate snapshot + redirect cue.

Renders `.ai-state/metrics_reports/METRICS_REPORT_*.json` artifacts at a
fidelity matching the doc-manifest schema reference's "Existing dashboard
page" framing: a quick aggregate snapshot (top-level health metrics +
run metadata) plus a prominent pointer to the dedicated **Metrics** page
for the full trend-aware visualization.

This deliberately does not duplicate `pages/metrics.py` — that page has
trend charts, hotspot tables, coverage breakdowns, and per-collector
deep dives. The renderer here is the documentation-sidebar landing card:
"here are the headlines; for the full picture, open the Metrics page".

The full JSON body is available in a collapsed expander for quick
inspection without leaving the documentation flow.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st


# Aggregate keys we promote into the headline metric strip, in display order.
# Each entry: (json_key, label, format_callable_or_None).
_HEADLINE_METRICS: tuple[tuple[str, str, Any], ...] = (
    ("file_count", "Files", lambda v: f"{int(v):,}"),
    ("ccn_p95", "CCN p95", lambda v: f"{v:.1f}"),
    ("cognitive_p95", "Cognitive p95", lambda v: f"{v:.1f}"),
    ("coverage_line_pct", "Coverage", lambda v: f"{v:.1f}%"),
    ("cyclic_deps", "Cyclic deps", lambda v: f"{int(v):,}"),
    ("churn_total_90d", "Churn (90d)", lambda v: f"{int(v):,}"),
    ("change_entropy_90d", "Entropy (90d)", lambda v: f"{v:.1f}"),
)


def render(surface: dict[str, Any], project_root: Path) -> None:
    path = project_root / surface["path"]
    if not path.exists():
        st.error(f"Source file not found: `{surface['path']}`")
        return

    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001 — surface read errors clearly
        st.error(f"Failed to read `{surface['path']}`: {exc}")
        return

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        st.error(f"`{surface['path']}` is not valid JSON: {exc}")
        st.code(text, language="json")
        return

    st.markdown(f"## 📊 {surface.get('title', path.name)}")
    st.caption(f"Metrics snapshot · source: `{surface['path']}`")
    st.info(
        "For trend lines, hotspot tables, and per-collector deep dives, open "
        "the **Metrics** page from the main navigation."
    )

    _render_run_metadata(data)
    _render_headline_metrics(data.get("aggregate", {}))
    _render_full_json_expander(data)


def _render_run_metadata(data: dict[str, Any]) -> None:
    meta = data.get("run_metadata") or {}
    aggregate = data.get("aggregate") or {}
    chips: list[str] = []
    if data.get("schema_version"):
        chips.append(f"schema `{data['schema_version']}`")
    if aggregate.get("commit_sha"):
        chips.append(f"commit `{str(aggregate['commit_sha'])[:8]}`")
    if meta.get("window_days"):
        chips.append(f"window `{meta['window_days']}d`")
    if meta.get("python_version"):
        chips.append(f"python `{meta['python_version']}`")
    if meta.get("wall_clock_seconds"):
        chips.append(f"runtime `{meta['wall_clock_seconds']:.1f}s`")
    if chips:
        st.caption(" · ".join(chips))


def _render_headline_metrics(aggregate: dict[str, Any]) -> None:
    if not aggregate:
        st.caption("(No `aggregate` block in this report.)")
        return

    presentable = [
        (key, label, formatter)
        for key, label, formatter in _HEADLINE_METRICS
        if key in aggregate and aggregate[key] is not None
    ]
    if not presentable:
        st.caption("(No headline metrics resolvable from the `aggregate` block.)")
        return

    st.markdown("### Headline metrics")
    columns = st.columns(min(len(presentable), 4))
    for index, (key, label, formatter) in enumerate(presentable):
        try:
            display = formatter(aggregate[key])
        except (TypeError, ValueError):
            display = str(aggregate[key])
        columns[index % len(columns)].metric(label, display)


def _render_full_json_expander(data: dict[str, Any]) -> None:
    with st.expander("Full report JSON", expanded=False):
        st.json(data)


__all__ = ["render"]
