"""Diátaxis explanation shell — wide-text + illustration-heavy wrapper.

Renders MD surfaces with `diataxis: explanation` (or `concepts`) frontmatter
in a reading-mode layout that complements `reference_shell`'s lookup-mode
layout. Where reference_shell adds sortable tables for scan-and-jump, this
shell adds three reading-mode affordances:

- **Reading-time estimate** in the header chips
- **Freshness signal** harvested from an AaC `last-reviewed=` HTML comment
- **Related-reading sidebar** harvested from a `## See Also` (or
  `## Further Reading` / `## Related`) H2 section

The body is rendered inline as native markdown (preserves prose flow). MD
is read live from disk per `rules/writing/html-output-conventions.md`.

Used for `docs/aac-dac.md`, `docs/claude-ecosystem-learning-resources.md`,
`docs/concepts.md`, `docs/decision-tracking.md`, `docs/memory-architecture.md`.
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


# Standard reading-speed assumption. 230 wpm is the conventional midpoint
# for technical prose; not perfectly accurate but accurate-enough to give
# the reader a useful order-of-magnitude.
_WORDS_PER_MINUTE = 230

# AaC freshness metadata: <!-- aac:authored owner=... last-reviewed=YYYY-MM-DD ... -->
_AAC_LAST_REVIEWED = re.compile(
    r"<!--\s*aac:authored[^>]*last-reviewed=(\d{4}-\d{2}-\d{2})[^>]*-->",
    re.IGNORECASE,
)

# H2 titles we treat as "related reading" sections worth promoting to the sidebar.
_RELATED_SECTION_TITLES = frozenset(
    {"see also", "further reading", "related", "related reading"}
)

# Bulleted-list line: "- <rest>". Trailing prose after a link is common in
# real See-Also sections (e.g. "- [label](url) — explanation"), so detect
# the link separately rather than requiring it to consume the whole line.
_BULLET_LINE = re.compile(r"^\s*[-*]\s+(?P<rest>.+?)\s*$")
_FIRST_LINK = re.compile(r"\[(?P<label>[^\]]+)\]\((?P<url>[^)]+)\)")


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
    sections = split_h2_sections(body)

    _render_header(surface, title, summary, body)
    _render_sidebar(sections)
    _render_body(sections)


def _render_header(
    surface: dict[str, Any], title: str, summary: str | None, body: str
) -> None:
    st.markdown(f"## 💡 {title}")
    if summary and not summary.lstrip().startswith("<!--"):
        st.markdown(f"*{summary}*")

    chips: list[str] = [f"audience: {surface.get('audience', 'developer')}"]
    minutes = _reading_time_minutes(body)
    if minutes:
        chips.append(f"~{minutes} min read")
    last_reviewed = _extract_last_reviewed(body)
    if last_reviewed:
        chips.append(f"reviewed `{last_reviewed}`")
    chips.append(f"source: `{surface['path']}`")

    st.caption(" · ".join(chips))
    st.divider()


def _render_sidebar(sections: list[tuple[str, str]]) -> None:
    render_h2_toc_in_sidebar(
        sections, empty_message="(No H2 sections in this explanation.)"
    )

    related_links = _extract_related_links(sections)
    if related_links:
        with st.sidebar:
            st.divider()
            st.markdown("**Related reading**")
            for label, url in related_links:
                if url:
                    st.markdown(f"- [{label}]({url})")
                else:
                    st.markdown(f"- {label}")


def _render_body(sections: list[tuple[str, str]]) -> None:
    render_anchored_body(sections)


# ---------------------------------------------------------------------------
# Body-derived header chips
# ---------------------------------------------------------------------------


def _reading_time_minutes(body: str) -> int:
    words = len(re.findall(r"\b\w+\b", body))
    if words == 0:
        return 0
    return max(1, round(words / _WORDS_PER_MINUTE))


def _extract_last_reviewed(body: str) -> str | None:
    match = _AAC_LAST_REVIEWED.search(body)
    return match.group(1) if match else None


# ---------------------------------------------------------------------------
# Related-reading harvest
# ---------------------------------------------------------------------------


def _extract_related_links(
    sections: list[tuple[str, str]],
) -> list[tuple[str, str | None]]:
    """Pull bulleted links out of any 'See Also' / 'Further Reading' /
    'Related' H2 section. Returns [(label, url_or_None), ...] in source order.
    """
    for heading, section_body in sections:
        if not heading:
            continue
        if heading.strip().lower() not in _RELATED_SECTION_TITLES:
            continue
        return _parse_bullet_list(section_body)
    return []


def _parse_bullet_list(text: str) -> list[tuple[str, str | None]]:
    items: list[tuple[str, str | None]] = []
    for line in text.split("\n"):
        bullet = _BULLET_LINE.match(line)
        if not bullet:
            continue
        rest = bullet.group("rest").strip()
        if not rest or rest.startswith(">"):
            continue
        link = _FIRST_LINK.search(rest)
        if link:
            items.append((link.group("label").strip(), link.group("url").strip()))
        else:
            items.append((rest, None))
    return items


__all__ = ["render"]
