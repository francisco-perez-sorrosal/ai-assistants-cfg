"""Idea grid renderer — proposal cards + ledger status tabs.

Renders two related artifact shapes per the doc-manifest schema reference:

- **Idea proposal** (`.ai-work/<slug>/IDEA_PROPOSAL.md`) — single-feature
  proposal with Summary, Problem/Opportunity, Proposed Solution, etc.
  The Summary section is pulled to a prominent callout above the TOC.
- **Idea ledger** (`.ai-state/idea_ledgers/IDEA_LEDGER_*.md`) — running
  catalog grouped under Implemented / Pending / Discarded / Future Paths.
  Status sections become `st.tabs` with top-bullet counts as tab labels;
  any non-status H2 (e.g. "Migration provenance") goes into a collapsed
  expander below the tabs.

Shape is detected from the H2 heading set: when at least two of the four
canonical status sections appear, it's a ledger; otherwise it's a proposal.

MD body is read live from disk per `rules/writing/html-output-conventions.md`.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import streamlit as st

from streamlit_app.components._base import (
    read_md,
    split_h2_sections,
    surface_summary,
    surface_title,
)
from streamlit_app.components._render_helpers import (
    render_anchored_body,
    render_h2_toc_in_sidebar,
)


_LEDGER_STATUS_SECTIONS: tuple[str, ...] = (
    "Implemented",
    "Pending",
    "Discarded",
    "Future Paths",
)
_LEDGER_STATUS_LOWER = frozenset(s.lower() for s in _LEDGER_STATUS_SECTIONS)

# A "top-level" bullet line starts at column 0 (no leading whitespace) and
# uses `-` or `*` followed by a space and a non-space char.
_TOP_BULLET = re.compile(r"^[-*]\s+\S")


def render(surface: dict[str, Any], project_root: Path) -> None:
    path = project_root / surface["path"]
    if not path.exists():
        st.error(f"Source file not found: `{surface['path']}`")
        return

    try:
        _, body = read_md(path)
    except Exception as exc:  # noqa: BLE001 — surface read errors clearly
        st.error(f"Failed to parse `{surface['path']}`: {exc}")
        return

    sections = split_h2_sections(body)

    if _looks_like_ledger(sections):
        _render_ledger(surface, body, sections)
    else:
        _render_proposal(surface, body, sections)


def _looks_like_ledger(sections: list[tuple[str, str]]) -> bool:
    titles = {t.strip().lower() for t, _ in sections if t}
    return len(titles & _LEDGER_STATUS_LOWER) >= 2


# ---------------------------------------------------------------------------
# Proposal shape — single-card view
# ---------------------------------------------------------------------------


def _render_proposal(
    surface: dict[str, Any], body: str, sections: list[tuple[str, str]]
) -> None:
    title = surface_title(surface, body)
    summary = surface_summary(surface, body)

    st.markdown(f"## 💡 {title}")
    if summary and not summary.lstrip().startswith("<!--"):
        st.markdown(f"*{summary}*")
    st.caption(f"Idea Proposal · source: `{surface['path']}`")
    st.divider()

    summary_section = next(
        (b for t, b in sections if t.strip().lower() == "summary" and b),
        None,
    )
    if summary_section:
        st.info(summary_section)

    skip = frozenset({"summary"})
    render_h2_toc_in_sidebar(
        sections,
        empty_message="(No additional H2 sections.)",
        skip_titles=skip,
    )
    render_anchored_body(sections, skip_titles=skip)


# ---------------------------------------------------------------------------
# Ledger shape — status tabs + counts
# ---------------------------------------------------------------------------


def _render_ledger(
    surface: dict[str, Any], body: str, sections: list[tuple[str, str]]
) -> None:
    title = surface_title(surface, body)

    st.markdown(f"## 📋 {title}")
    st.caption(f"Idea Ledger · source: `{surface['path']}`")

    by_title_lower = {t.strip().lower(): b for t, b in sections if t}
    counts = {
        status: _count_top_bullets(by_title_lower.get(status.lower(), ""))
        for status in _LEDGER_STATUS_SECTIONS
    }

    columns = st.columns(len(_LEDGER_STATUS_SECTIONS))
    for col, status in zip(columns, _LEDGER_STATUS_SECTIONS):
        col.metric(status, counts[status])
    st.divider()

    pre_h2 = next((b for t, b in sections if not t and b), "")
    if pre_h2:
        st.markdown(pre_h2)
        st.divider()

    tabs = st.tabs(
        [f"{status} ({counts[status]})" for status in _LEDGER_STATUS_SECTIONS]
    )
    for tab, status in zip(tabs, _LEDGER_STATUS_SECTIONS):
        with tab:
            section_body = by_title_lower.get(status.lower(), "")
            if section_body:
                st.markdown(section_body)
            else:
                st.caption(f"(No items recorded under '{status}'.)")

    other_sections = [
        (t, b)
        for t, b in sections
        if t and t.strip().lower() not in _LEDGER_STATUS_LOWER
    ]
    if other_sections:
        with st.expander("Other sections", expanded=False):
            for heading, section_body in other_sections:
                st.markdown(f"### {heading}")
                st.markdown(section_body)


def _count_top_bullets(text: str) -> int:
    return sum(1 for line in text.split("\n") if _TOP_BULLET.match(line))


__all__ = ["render"]
