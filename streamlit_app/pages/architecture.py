"""Architecture page — design-target ARCHITECTURE.md + LikeC4 SVG diagrams.

Renders three content surfaces in order:
  1. LikeC4 SVG diagrams from ``docs/diagrams/`` (skipped if none exist).
  2. Architect-facing ``ARCHITECTURE.md`` — sections rendered with visual
     ``aac:generated`` / ``aac:authored`` badges.
  3. Developer-facing ``docs/architecture.md`` — rendered as plain markdown.

Empty-state is shown when all three surfaces are absent (fresh project or no
architecture pass yet).
"""

from __future__ import annotations

import re

import streamlit as st
import streamlit.components.v1 as components

from streamlit_app.config import get_config
from streamlit_app.data import cache, discovery
from streamlit_app.widgets import artifact_card, empty_state

# Path to the architecture-as-code skill (educational affordance).
_ARCH_SKILL_REL = "skills/software-planning/SKILL.md"

# Fence markers used in ARCHITECTURE.md bodies.
# Matches <!-- aac:generated --> and <!-- aac:generated key=value ... --> variants.
_FENCE_OPEN = re.compile(r"<!--\s*aac:(generated|authored)(?:\s[^>]*)?\s*-->")
# Matches <!-- /aac:generated --> and <!-- aac:end --> close markers.
_FENCE_CLOSE = re.compile(r"<!--\s*(?:/aac:(generated|authored)|aac:end)\s*-->")

# Badge prefixes rendered in artifact_card titles.
_BADGE_GENERATED = "Generated"
_BADGE_AUTHORED = "Authored"


# ---------------------------------------------------------------------------
# AaC fence helpers
# ---------------------------------------------------------------------------


def _split_aac_fences(body: str) -> list[tuple[str, str]]:
    """Split *body* into ``[(kind, content), ...]`` chunks by aac fence pairs.

    Regions inside ``<!-- aac:generated -->`` … ``<!-- /aac:generated -->``
    become ``("generated", content)`` tuples.  Regions inside
    ``<!-- aac:authored -->`` … ``<!-- /aac:authored -->`` become
    ``("authored", content)`` tuples.  Text outside any fence becomes
    ``("plain", content)`` tuples.

    Unknown or malformed fences are treated as plain text.  Empty chunks
    are omitted from the result.
    """
    chunks: list[tuple[str, str]] = []
    current_kind = "plain"
    current_lines: list[str] = []

    for line in body.splitlines(keepends=True):
        open_match = _FENCE_OPEN.match(line.strip())
        close_match = _FENCE_CLOSE.match(line.strip())

        if open_match:
            # Flush current chunk before entering a new fence.
            if current_lines:
                chunks.append((current_kind, "".join(current_lines)))
                current_lines = []
            current_kind = open_match.group(1)
        elif close_match:
            # Flush the fenced chunk.
            if current_lines:
                chunks.append((current_kind, "".join(current_lines)))
                current_lines = []
            current_kind = "plain"
        else:
            current_lines.append(line)

    # Flush the final chunk.
    if current_lines:
        chunks.append((current_kind, "".join(current_lines)))

    # Remove empty chunks.
    return [(kind, content) for kind, content in chunks if content.strip()]


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------


def _render_svgs(svgs: list) -> None:
    """Render LikeC4 SVG diagrams using streamlit.components.v1.html."""
    st.subheader("Architecture Diagrams")
    config = get_config()
    for svg_path in svgs:
        try:
            rel = svg_path.relative_to(config.project_root)
        except ValueError:
            rel = svg_path.name
        st.markdown(f"**{rel}**")
        try:
            svg_text = svg_path.read_text(encoding="utf-8")
            components.html(svg_text, height=600, scrolling=True)
        except Exception:  # noqa: BLE001
            st.error(f"Could not render `{svg_path.name}`")


def _render_architecture_md(arch_path) -> None:
    """Render the architect-facing ARCHITECTURE.md with aac fence badges."""
    _, body = cache.cached_parse_frontmatter(str(arch_path), cache.mtime_of(arch_path))

    st.subheader("Architecture (Design Target)")
    st.caption(
        "Architect-facing design document — abstracts above concrete code."
        " Sections tagged **Generated** are auto-produced by the AaC pipeline;"
        " sections tagged **Authored** are human-curated."
    )

    chunks = _split_aac_fences(body)

    if not chunks:
        st.markdown(body)
        return

    for kind, content in chunks:
        if kind == "generated":
            _render_aac_chunk(content, badge=_BADGE_GENERATED)
        elif kind == "authored":
            _render_aac_chunk(content, badge=_BADGE_AUTHORED)
        else:
            st.markdown(content)


def _render_aac_chunk(content: str, badge: str) -> None:
    """Render one aac fence region with a visual badge title."""
    # Extract first heading as title when possible.
    first_heading = ""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            first_heading = stripped.lstrip("#").strip()
            break

    title = f"{badge}: {first_heading}" if first_heading else badge
    artifact_card.artifact_card(
        title=title,
        body_md=content,
        expanded=True,
    )


def _render_developer_architecture(dev_path) -> None:
    """Render the developer-facing docs/architecture.md."""
    st.subheader("Architecture Guide (Developer-Facing)")
    st.caption(
        "Code-verified component map for daily navigation (`docs/architecture.md`)."
    )

    _, body = cache.cached_parse_frontmatter(str(dev_path), cache.mtime_of(dev_path))
    st.markdown(body)


# ---------------------------------------------------------------------------
# Page entry point
# ---------------------------------------------------------------------------


def render() -> None:
    """Render the Architecture page.

    Surfaces (rendered in order when present):
      1. LikeC4 SVG diagrams — embedded via components.html.
      2. ARCHITECTURE.md — architect-facing, with aac fence badges.
      3. docs/architecture.md — developer-facing, plain markdown.

    Degrades to empty_state when none of the three surfaces are present.
    """
    config = get_config()

    arch_md = discovery.find_design_md(config.project_root)
    dev_arch = discovery.find_developer_architecture(config.project_root)
    svgs = discovery.list_likec4_svgs(config.project_root)

    st.title("Architecture")
    st.caption(
        "Design-target ARCHITECTURE.md, LikeC4 diagrams,"
        " and the developer-facing architecture guide."
    )

    skill_path = str(config.project_root / _ARCH_SKILL_REL)

    if not arch_md and not dev_arch and not svgs:
        empty_state.empty_state(
            artifact_name="DESIGN.md",
            producer_path=skill_path,
            explanation=(
                "No architecture artifacts found. Run a pipeline with the"
                " `systems-architect` agent to generate `DESIGN.md`"
                " and `docs/architecture.md`."
            ),
        )
        return

    if svgs:
        _render_svgs(svgs)

    if arch_md:
        _render_architecture_md(arch_md)

    if dev_arch:
        _render_developer_architecture(dev_arch)
