"""Shared Streamlit-side helpers for H2-TOC + anchored-body rendering.

Six renderers (`reference_shell`, `explanation_shell`, `how_to_shell`,
`verification_report`, `idea_grid` proposal arm, and `architecture_explorer`'s
markdown panes) shared the same skeleton: a sidebar `**Sections**` H2 TOC
plus an inline body with declarative anchor spans (`<span id='...' />`)
for fragment navigation. This module factors that skeleton out so the
renderers stay focused on their distinguishing affordances.

Distinct from `_base.py`, which is the pure-Python parsing module
(no Streamlit imports). These helpers do call into `streamlit`, so they
live separately to preserve `_base.py`'s testability without a Streamlit
context.

The renderers `adr_card` (uses H2 expanders rather than anchor spans),
`tutorial_shell` (numbers each H2 as "Step N — heading"), `plan_view`
(H3-based), `default_markdown` (no TOC, no anchors), and `metrics_view`
(JSON) deliberately keep their bespoke rendering and do not import here.
"""

from __future__ import annotations

import streamlit as st

from streamlit_app.components._base import heading_to_anchor


def render_h2_toc_in_sidebar(
    sections: list[tuple[str, str]],
    *,
    label: str = "Sections",
    empty_message: str = "(No H2 sections.)",
    skip_titles: frozenset[str] = frozenset(),
) -> None:
    """Render an H2 anchor-list TOC inside `st.sidebar`.

    `skip_titles` is a frozenset of lowercase H2 titles to omit from the
    TOC (used by `idea_grid` proposal to hide "Summary" since it is
    already promoted to an `st.info` callout above the body).
    """
    visible = [
        title
        for title, _ in sections
        if title and title.strip().lower() not in skip_titles
    ]
    with st.sidebar:
        st.markdown(f"**{label}**")
        if not visible:
            st.caption(empty_message)
            return
        for heading in visible:
            anchor = heading_to_anchor(heading)
            st.markdown(f"- [{heading}](#{anchor})")


def render_anchored_body(
    sections: list[tuple[str, str]],
    *,
    skip_titles: frozenset[str] = frozenset(),
) -> None:
    """Render H2 sections inline with declarative anchor spans.

    Pre-H2 content (the first non-empty block before any H2) is rendered
    first as a contiguous markdown block. Each subsequent H2 emits a
    `<span id='...' />` anchor (declarative HTML only — no JavaScript per
    `rules/writing/html-output-conventions.md`), then a level-3 heading
    bearing the section title, then the section body.

    `skip_titles` is a frozenset of lowercase titles to omit (parallels
    `render_h2_toc_in_sidebar`).
    """
    pre_h2 = next((body for title, body in sections if not title and body), "")
    if pre_h2:
        st.markdown(pre_h2)

    for heading, section_body in sections:
        if not heading or heading.strip().lower() in skip_titles:
            continue
        anchor = heading_to_anchor(heading)
        st.markdown(f"<span id='{anchor}'></span>", unsafe_allow_html=True)
        st.markdown(f"### {heading}")
        st.markdown(section_body)


__all__ = ["render_h2_toc_in_sidebar", "render_anchored_body"]
