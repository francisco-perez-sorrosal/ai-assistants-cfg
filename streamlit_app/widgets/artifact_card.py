"""Artifact card widget — the unit of artifact rendering."""

from __future__ import annotations

import streamlit as st

from streamlit_app.widgets import educational as _educational_mod

# Maximum number of metadata keys to display in the key/value table.
_MAX_METADATA_ROWS = 10


def artifact_card(
    title: str,
    body_md: str,
    what_is_this: str | None = None,
    metadata: dict | None = None,
    expanded: bool = False,
) -> None:
    """Render a single artifact as a card.

    Args:
        title: heading shown at the top of the card (rendered as st.subheader).
        body_md: markdown body (caller must have stripped frontmatter —
            Convention 4).
        what_is_this: path to a producer skill/rule/agent file. If given,
            renders the educational popover via
            widgets.educational.educational(target_path).
        metadata: optional frontmatter dict; rendered as a small key/value
            table ABOVE the body when present. Capped at
            ``_MAX_METADATA_ROWS`` most relevant keys.
        expanded: if True, body shown immediately; if False, wrapped in
            st.expander.
    """
    title_col, popover_col = st.columns([8, 2])

    with title_col:
        st.subheader(title)

    if what_is_this is not None:
        with popover_col:
            _educational_mod.educational(what_is_this)

    if metadata:
        rows = list(metadata.items())[:_MAX_METADATA_ROWS]
        keys = [r[0] for r in rows]
        values = [str(r[1]) for r in rows]
        st.table({"Key": keys, "Value": values})

    if expanded:
        st.markdown(body_md)
    else:
        with st.expander("View body", expanded=False):
            st.markdown(body_md)
