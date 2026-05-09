"""Fallback renderer — plain `st.markdown` of the surface body.

Used when no specialized renderer is registered for a surface, or when the
specialized renderer is not yet implemented (Tier 2/3 renderers route here
until shipped).

Reads MD live from disk per the convention rule (`rules/writing/
html-output-conventions.md`) — never pre-bakes content.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from streamlit_app.components._base import (
    read_md,
    surface_summary,
    surface_title,
)


def render(surface: dict[str, Any], project_root: Path) -> None:
    """Render a markdown surface as-is via st.markdown."""
    path = project_root / surface["path"]

    if not path.exists():
        st.error(f"Source file not found: `{path.relative_to(project_root)}`")
        return

    if surface.get("type", "markdown") == "markdown":
        try:
            _, body = read_md(path)  # frontmatter already consumed by manifest
        except Exception as exc:  # noqa: BLE001 — surface read errors clearly
            st.error(f"Failed to parse `{surface['path']}`: {exc}")
            return

        title = surface_title(surface, body)
        summary = surface_summary(surface, body)

        # Header band: title + diataxis chip + audience chip
        chips = []
        if surface.get("diataxis"):
            chips.append(f"`diataxis: {surface['diataxis']}`")
        if surface.get("audience"):
            chips.append(f"`audience: {surface['audience']}`")
        chips.append(f"`{surface['path']}`")

        st.markdown(f"### {title}")
        if summary:
            st.caption(summary)
        st.caption(" · ".join(chips))
        st.divider()

        # Body (MD inlined per the convention)
        st.markdown(body)
        return

    # Non-markdown: render the raw text in a code block (yaml/json/etc.)
    st.markdown(f"### {surface_title(surface)}")
    st.caption(f"`{surface['path']}` · type: `{surface.get('type', 'unknown')}`")
    st.divider()

    try:
        text = path.read_text()
    except Exception as exc:  # noqa: BLE001
        st.error(f"Failed to read `{surface['path']}`: {exc}")
        return

    if surface.get("type") == "json":
        import json

        try:
            data = json.loads(text)
            st.json(data)
        except json.JSONDecodeError:
            st.code(text, language="json")
    elif surface.get("type") == "yaml":
        st.code(text, language="yaml")
    else:
        st.code(text)


__all__ = ["render"]
