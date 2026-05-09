"""Diátaxis tutorial shell — progress-through-steps wrapper.

Renders MD surfaces with `diataxis: tutorial` frontmatter. Adds:
- A header band with the tutorial title + summary
- A sticky table-of-contents from H2 headings (the "steps")
- The body inline below, with anchored navigation
- A "what you'll have built when done" sidebar (when explicit in frontmatter)

Used for `docs/getting-started.md`, `docs/greenfield-onboarding.md`,
`docs/existing-project-onboarding.md`, `docs/ml-training-onramp.md`.

MD body is read from disk live (per the convention rule); never duplicated.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from streamlit_app.components._base import (
    heading_to_anchor,
    read_md,
    split_h2_sections,
    surface_summary,
    surface_title,
)


def render(surface: dict[str, Any], project_root: Path) -> None:
    path = project_root / surface["path"]
    if not path.exists():
        st.error(f"Source file not found: `{path.relative_to(project_root)}`")
        return

    try:
        frontmatter, body = read_md(path)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Failed to parse `{surface['path']}`: {exc}")
        return

    title = surface_title(surface, body)
    summary = surface_summary(surface, body)

    # ── Header band ────────────────────────────────────────────────────────
    st.markdown(f"## 📚 {title}")
    if summary:
        st.markdown(f"*{summary}*")
    st.caption(
        f"Tutorial · audience: {frontmatter.get('audience', 'developer')} · "
        f"source: `{surface['path']}`"
    )
    st.divider()

    # ── Sidebar: step navigation + what-you'll-build ──────────────────────
    sections = split_h2_sections(body)
    step_sections = [(t, b) for t, b in sections if t]  # exclude pre-H2 content

    with st.sidebar:
        st.markdown("**Steps**")
        if step_sections:
            for i, (heading, _) in enumerate(step_sections, start=1):
                anchor = heading_to_anchor(heading)
                st.markdown(f"{i}. [{heading}](#{anchor})")
        else:
            st.caption("(No H2 sections in this tutorial)")

        # Explicit "what you'll build" hook — opt-in via frontmatter
        if frontmatter.get("outcome"):
            st.divider()
            st.markdown("**What you'll have built**")
            st.markdown(str(frontmatter["outcome"]))

    # ── Pre-H2 content (intro paragraph, prereqs) ─────────────────────────
    pre_h2 = [b for t, b in sections if not t]
    if pre_h2:
        st.markdown(pre_h2[0])
        st.divider()

    # ── Step bodies, each in its own anchor target ────────────────────────
    for i, (heading, section_body) in enumerate(step_sections, start=1):
        anchor = heading_to_anchor(heading)
        # Streamlit doesn't natively support fragment anchors; emit one via
        # an inline HTML span the browser can target. Safe — declarative HTML
        # only (no JS) per the convention rule.
        st.markdown(
            f"<span id='{anchor}'></span>",
            unsafe_allow_html=True,
        )
        st.markdown(f"### Step {i} — {heading}")
        st.markdown(section_body)
        if i < len(step_sections):
            st.divider()


__all__ = ["render"]
