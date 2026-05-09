"""IMPLEMENTATION_PLAN.md renderer — step cards with WIP overlay.

Renders an in-flight pipeline's `IMPLEMENTATION_PLAN.md` as a series of step
cards. When `WIP.md` exists alongside (in the same workshop directory),
overlays per-step status (current / pending / completed / blocked) for
at-a-glance pipeline progress.

Used for `.ai-work/<active-slug>/IMPLEMENTATION_PLAN.md`. Surface descriptor
should set `renderer: plan_view` in the manifest.

Heuristics:
- Steps are ## or ### sections whose title starts with "Step" (case-insensitive)
- Status overlay reads `parse_wip()` and matches by step number / title
- "Acceptance Criteria", "Verification", "Files" sub-sections are pulled into
  expandable cards within each step

MD source is read live from disk per the convention; WIP.md is parsed at
render time, never duplicated.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import streamlit as st

from streamlit_app.components._base import (
    read_md,
    split_h3_sections,
    surface_summary,
    surface_title,
)
from streamlit_app.data.parsers import parse_wip


_STEP_HEADING_RE = re.compile(
    r"^step\s+(\d+(?:\.\d+)?)\s*[—:.\-]?\s*(.*)$", re.IGNORECASE
)


def _parse_step_heading(heading: str) -> tuple[str | None, str]:
    """Return (step_id, label) from an H3 like `Step 2: Atomic rename`.

    If the heading is not a step heading, returns (None, heading)."""
    m = _STEP_HEADING_RE.match(heading.strip())
    if not m:
        return (None, heading.strip())
    return (m.group(1), m.group(2).strip())


def _status_emoji(status: str) -> str:
    return {
        "completed": "✅",
        "current": "🔄",
        "in_progress": "🔄",
        "blocked": "⛔",
        "pending": "⏳",
    }.get(status.lower(), "⏳")


def _wip_status_for_step(
    wip_data: dict[str, Any], step_id: str | None, label: str
) -> str:
    """Best-effort match between a plan step and a WIP.md checklist entry."""
    if not wip_data or not step_id:
        return "pending"
    for item in wip_data.get("checklist", []):
        item_step_id = str(item.get("step_id", "")).strip()
        item_label = str(item.get("label", "")).strip().lower()
        if item_step_id == step_id:
            if item.get("checked"):
                return "completed"
            if item.get("current"):
                return "current"
            return "pending"
        # Fall back to label substring match if step ids don't align
        if label and label.lower() in item_label and item.get("checked"):
            return "completed"
    return "pending"


def render(surface: dict[str, Any], project_root: Path) -> None:
    plan_path = project_root / surface["path"]
    if not plan_path.exists():
        st.error(f"Source file not found: `{plan_path.relative_to(project_root)}`")
        return

    try:
        frontmatter, body = read_md(plan_path)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Failed to parse `{surface['path']}`: {exc}")
        return

    title = surface_title(surface, body)
    summary = surface_summary(surface, body)

    # ── Header band ────────────────────────────────────────────────────────
    st.markdown(f"## 🗺️ {title}")
    if summary:
        st.markdown(f"*{summary}*")
    st.caption(f"Implementation Plan · source: `{surface['path']}`")

    # ── WIP overlay: if WIP.md exists alongside, parse it ─────────────────
    workshop_dir = plan_path.parent
    wip_path = workshop_dir / "WIP.md"
    wip_data: dict[str, Any] = {}
    if wip_path.exists():
        try:
            wip_data = parse_wip(wip_path)
        except Exception:  # noqa: BLE001 — bad WIP.md is non-fatal
            wip_data = {}

    # Status counts for the header
    sections = split_h3_sections(body)
    step_sections = [
        (label, section_body, _parse_step_heading(label))
        for label, section_body in sections
        if label and _STEP_HEADING_RE.match(label.strip())
    ]

    if step_sections:
        statuses = [
            _wip_status_for_step(wip_data, step_id, step_label)
            for _, _, (step_id, step_label) in step_sections
        ]
        n_total = len(step_sections)
        n_done = sum(1 for s in statuses if s == "completed")
        n_current = sum(1 for s in statuses if s == "current")

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Steps total", n_total)
        col_b.metric("Completed", n_done)
        col_c.metric("In-flight", n_current)

    st.divider()

    # ── Pre-H3 content (Goal, Acceptance Criteria header, etc.) ──────────
    pre_h3 = [b for t, b in sections if not t]
    if pre_h3:
        with st.expander(
            "📋 Plan overview (goal, acceptance criteria, scope)", expanded=False
        ):
            st.markdown(pre_h3[0])

    # ── Step cards ────────────────────────────────────────────────────────
    if not step_sections:
        st.info("No `### Step N: ...` headings detected in this plan.")
        st.markdown(body)
        return

    for label, section_body, (step_id, step_label) in step_sections:
        status = _wip_status_for_step(wip_data, step_id, step_label)
        emoji = _status_emoji(status)

        header = (
            f"{emoji} **Step {step_id}** — {step_label}"
            if step_id
            else f"{emoji} **{label}**"
        )
        is_current = status == "current"

        with st.expander(header, expanded=is_current):
            # Status chip + raw label
            chips = [f"`status: {status}`"]
            if step_id:
                chips.append(f"`step_id: {step_id}`")
            st.caption(" · ".join(chips))
            st.markdown(section_body)


__all__ = ["render"]
