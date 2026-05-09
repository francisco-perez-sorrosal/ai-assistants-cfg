"""Diátaxis reference shell — anchored-nav + sortable-tables wrapper.

Renders MD surfaces with `diataxis: reference` frontmatter. Adds:
- A header band with the title, summary, and source path
- A sidebar TOC built from H2 headings (anchor-jump targets)
- The body rendered inline as native markdown (preserves prose flow)
- A "Sortable views" expander surfacing any table with at least
  `_SORTABLE_TABLE_THRESHOLD` rows as an interactive `st.dataframe`

Used for `docs/README.md`, `docs/architecture-diagrams.md`,
`docs/diagrams/README.md`, `docs/metrics/README.md`, and
`docs/spec-driven-development.md`.

MD body is read live from disk per `rules/writing/html-output-conventions.md`.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from streamlit_app.components._base import (
    heading_to_anchor,
    read_md,
    split_h2_sections,
    surface_summary,
    surface_title,
)


# Tables with at least this many data rows render as sortable dataframes
# in addition to their inline markdown form. Smaller tables stay inline
# only — sorting a 3-row table is friction, not value.
_SORTABLE_TABLE_THRESHOLD = 8


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

    title = surface_title(surface, body)
    summary = surface_summary(surface, body)

    st.markdown(f"## 📖 {title}")
    if summary:
        st.markdown(f"*{summary}*")
    st.caption(
        f"Reference · audience: {surface.get('audience', 'developer')} · "
        f"source: `{surface['path']}`"
    )
    st.divider()

    sections = split_h2_sections(body)
    _render_sidebar_toc(sections)
    _render_body_inline(sections)

    sortable = _collect_sortable_tables(body, sections)
    if sortable:
        _render_sortable_views(sortable)


def _render_sidebar_toc(sections: list[tuple[str, str]]) -> None:
    h2_titles = [t for t, _ in sections if t]
    with st.sidebar:
        st.markdown("**Sections**")
        if not h2_titles:
            st.caption("(No H2 sections in this reference.)")
            return
        for heading in h2_titles:
            anchor = heading_to_anchor(heading)
            st.markdown(f"- [{heading}](#{anchor})")


def _render_body_inline(sections: list[tuple[str, str]]) -> None:
    pre_h2 = next((b for t, b in sections if not t and b), "")
    if pre_h2:
        st.markdown(pre_h2)

    for heading, section_body in [(t, b) for t, b in sections if t]:
        anchor = heading_to_anchor(heading)
        # Streamlit doesn't natively support fragment anchors; emit one as
        # declarative HTML (no JS) per html-output-conventions.md.
        st.markdown(f"<span id='{anchor}'></span>", unsafe_allow_html=True)
        st.markdown(f"### {heading}")
        st.markdown(section_body)


# ---------------------------------------------------------------------------
# Sortable-table extraction
# ---------------------------------------------------------------------------


def _collect_sortable_tables(
    body: str, sections: list[tuple[str, str]]
) -> list[tuple[str, pd.DataFrame]]:
    """Return (section-label, dataframe) pairs for every table in `body`
    whose data-row count is at least `_SORTABLE_TABLE_THRESHOLD`.

    The section-label is the H2 heading the table lives under; tables in
    pre-H2 content are labelled "(intro)".
    """
    blocks = _find_table_blocks(body)
    if not blocks:
        return []

    # Map line numbers to their containing H2 section. Cheap pass: find each
    # H2 line and assign all subsequent lines to it until the next H2.
    line_to_section: dict[int, str] = {}
    current_section = "(intro)"
    for i, line in enumerate(body.split("\n")):
        if re.match(r"^##\s+", line):
            current_section = re.sub(r"^##\s+", "", line).strip()
        line_to_section[i] = current_section

    sortable: list[tuple[str, pd.DataFrame]] = []
    for start_line, lines in blocks:
        parsed = _parse_table(lines)
        if parsed is None:
            continue
        headers, rows = parsed
        if len(rows) < _SORTABLE_TABLE_THRESHOLD:
            continue
        section_label = line_to_section.get(start_line, "(intro)")
        try:
            df = pd.DataFrame(rows, columns=headers)
        except (ValueError, TypeError):
            continue
        sortable.append((section_label, df))
    return sortable


def _find_table_blocks(body: str) -> list[tuple[int, list[str]]]:
    """Return (start_line_index, table_lines) for every contiguous run of
    pipe-prefixed lines that includes at least a header + alignment row."""
    blocks: list[tuple[int, list[str]]] = []
    current: list[str] = []
    start = 0
    for i, line in enumerate(body.split("\n")):
        if line.lstrip().startswith("|"):
            if not current:
                start = i
            current.append(line)
        else:
            if len(current) >= 2:
                blocks.append((start, current))
            current = []
    if len(current) >= 2:
        blocks.append((start, current))
    return blocks


def _parse_table(lines: list[str]) -> tuple[list[str], list[list[str]]] | None:
    """Parse a markdown table block into (headers, rows).

    Returns None when the block doesn't validate as a markdown table —
    the second line must be the alignment row (dashes + optional colons).
    """
    if len(lines) < 2:
        return None
    headers = _split_row(lines[0])
    if not _is_alignment_row(lines[1]):
        return None
    rows = [_split_row(line) for line in lines[2:]]
    rows = [row for row in rows if any(cell.strip() for cell in row)]
    # Pad / truncate rows to header width so DataFrame construction succeeds.
    width = len(headers)
    rows = [(row + [""] * width)[:width] for row in rows]
    return headers, rows


def _split_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


_ALIGNMENT_CELL = re.compile(r"^\s*:?-+:?\s*$")


def _is_alignment_row(line: str) -> bool:
    cells = _split_row(line)
    return bool(cells) and all(_ALIGNMENT_CELL.match(cell) for cell in cells)


def _render_sortable_views(sortable: list[tuple[str, pd.DataFrame]]) -> None:
    st.divider()
    label = "🔢 Sortable views" if len(sortable) > 1 else "🔢 Sortable view"
    with st.expander(f"{label} ({len(sortable)})", expanded=False):
        st.caption(
            "Tables with at least "
            f"{_SORTABLE_TABLE_THRESHOLD} rows; click any column header to sort."
        )
        for section_label, df in sortable:
            st.markdown(f"**§ {section_label}**")
            st.dataframe(df, use_container_width=True, hide_index=True)


__all__ = ["render"]
