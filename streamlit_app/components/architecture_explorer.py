"""Architecture explorer renderer — three-pane Explanation / Reference / Diagrams.

Composes both architectural documents (`.ai-state/DESIGN.md` and
`docs/architecture.md`) and the rendered LikeC4 / D2 SVG diagrams into a
tabbed view per the doc-manifest schema reference.

Routed for surfaces with `renderer: architecture_explorer` (the two
canonical architecture markdowns). Whichever surface the user clicks from
the sidebar opens the same three-pane view — the routing is "land on
this artifact", the rendering is "show the architectural ensemble".

For the AaC fence-aware view of DESIGN.md (sections badged Generated vs
Authored via `artifact_card`), open the dedicated **Architecture** page
from the main navigation. This renderer keeps body rendering plain so it
does not duplicate the page's private fence-handling logic.

MD body is read live from disk per `rules/writing/html-output-conventions.md`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from streamlit_app.components._base import (
    heading_to_anchor,
    read_md,
    split_h2_sections,
)
from streamlit_app.components._render_helpers import render_anchored_body
from streamlit_app.data import discovery


def render(surface: dict[str, Any], project_root: Path) -> None:
    design_md = discovery.find_design_md(project_root)
    dev_arch = discovery.find_developer_architecture(project_root)
    svgs = discovery.list_likec4_svgs(project_root)

    st.markdown("## 🏛 Architecture Explorer")
    st.caption(
        "Composes architect-facing design (`DESIGN.md`), code-verified guide "
        "(`docs/architecture.md`), and rendered LikeC4 / D2 diagrams. "
        f"Entered from `{surface['path']}`."
    )
    st.caption(
        "For the AaC fence-aware view (Generated vs Authored badges), open "
        "the **Architecture** page from the main navigation."
    )

    if not (design_md or dev_arch or svgs):
        st.warning(
            "No architecture artifacts found. Run a pipeline with the "
            "`systems-architect` agent to generate `DESIGN.md` and "
            "`docs/architecture.md`."
        )
        return

    st.divider()

    tabs = st.tabs(
        [
            "📖 Explanation (DESIGN.md)" if design_md else "📖 Explanation",
            "📋 Reference (architecture.md)" if dev_arch else "📋 Reference",
            f"🗺 Diagrams ({len(svgs)})",
        ]
    )

    with tabs[0]:
        _render_md_pane(design_md, "`.ai-state/DESIGN.md` not present.")
    with tabs[1]:
        _render_md_pane(dev_arch, "`docs/architecture.md` not present.")
    with tabs[2]:
        _render_diagrams_pane(svgs, project_root)


def _render_md_pane(path: Path | None, missing_msg: str) -> None:
    if path is None:
        st.caption(missing_msg)
        return

    try:
        _, body = read_md(path)
    except Exception as exc:  # noqa: BLE001 — surface read errors clearly
        st.error(f"Failed to parse `{path}`: {exc}")
        return

    sections = split_h2_sections(body)
    h2_titles = [t for t, _ in sections if t]

    if h2_titles:
        with st.expander("📑 Sections", expanded=False):
            for heading in h2_titles:
                anchor = heading_to_anchor(heading)
                st.markdown(f"- [{heading}](#{anchor})")

    render_anchored_body(sections)


def _render_diagrams_pane(svgs: list[Path], project_root: Path) -> None:
    if not svgs:
        st.caption("No SVG diagrams found under `docs/diagrams/`.")
        return

    st.caption(
        f"{len(svgs)} rendered diagram(s) — first one open by default; click "
        "any other to inspect."
    )

    for index, svg_path in enumerate(svgs):
        try:
            rel = svg_path.relative_to(project_root)
        except ValueError:
            rel = Path(svg_path.name)

        # Group label: strip structural path components ("docs", "diagrams",
        # "rendered", "src") so the visible label is the diagram name plus
        # its parent group (e.g. "architecture / components").
        label_parts = [
            p for p in rel.parts if p not in ("docs", "diagrams", "rendered", "src")
        ]
        if label_parts:
            label_parts[-1] = label_parts[-1].removesuffix(".svg")
            # When a diagram dir holds a single SVG with the same stem as
            # the dir, "aac-dac-feedback-loop / aac-dac-feedback-loop" is
            # noise — collapse the redundant pair.
            if len(label_parts) >= 2 and label_parts[-1] == label_parts[-2]:
                label_parts.pop(-2)
        label = " / ".join(label_parts) if label_parts else rel.stem

        with st.expander(f"📐 {label}", expanded=(index == 0)):
            st.caption(f"`{rel}`")
            try:
                svg_text = svg_path.read_text(encoding="utf-8")
                components.html(svg_text, height=600, scrolling=True)
            except Exception:  # noqa: BLE001 — render errors are informative
                st.error(f"Could not render `{svg_path.name}`")


__all__ = ["render"]
