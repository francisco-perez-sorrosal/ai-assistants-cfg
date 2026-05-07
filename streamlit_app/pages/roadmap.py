"""Roadmap page — surfaces <project_root>/ROADMAP.md when present, empty state otherwise."""

from __future__ import annotations

import streamlit as st

from streamlit_app.config import get_config
from streamlit_app.data import cache, discovery
from streamlit_app.widgets import empty_state

_PRODUCER_REL = "skills/roadmap-synthesis/SKILL.md"


def render() -> None:
    """Render the Roadmap page.

    When ROADMAP.md is present: strips frontmatter and renders the body as
    markdown. When absent: delegates to the empty_state widget with a hint
    about the /roadmap slash command.
    """
    config = get_config()
    st.title("Roadmap")
    st.caption("Project-level direction and prioritized backlog.")

    roadmap_path = discovery.find_roadmap(config.project_root)
    if roadmap_path is None:
        empty_state.empty_state(
            artifact_name="ROADMAP.md",
            producer_path=str(config.project_root / _PRODUCER_REL),
            explanation=(
                "No `ROADMAP.md` at the project root."
                " Generate one with the `/roadmap` slash command"
                " (delegates to roadmap-cartographer)."
            ),
        )
        return

    _fm, body = cache.cached_parse_frontmatter(
        str(roadmap_path), cache.mtime_of(roadmap_path)
    )
    st.markdown(body)
