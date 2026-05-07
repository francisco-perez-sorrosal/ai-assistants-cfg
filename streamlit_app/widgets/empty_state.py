"""Empty-state widget — graceful degradation when source artifact is absent."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from streamlit_app.widgets import educational as _educational_mod


def empty_state(
    artifact_name: str,
    producer_path: str | None = None,
    explanation: str | None = None,
) -> None:
    """Render a graceful empty-state widget for missing artifacts.

    Args:
        artifact_name: human-readable name, e.g., "ROADMAP.md".
        producer_path: optional path to the skill/rule/agent that produces this
            artifact. If given, renders an educational popover via
            widgets.educational.educational(producer_path).
        explanation: optional override; if None, generated as
            "No {artifact_name} found in this project. It is produced by..."
    """
    if explanation is not None:
        message = explanation
    elif producer_path is not None:
        basename = Path(producer_path).name
        message = (
            f"No **{artifact_name}** found in this project."
            f" It is produced by `{basename}`."
            ' Click the "What is this?" button below to learn more.'
        )
    else:
        message = f"No **{artifact_name}** found in this project."

    st.info(message)

    if producer_path is not None:
        _educational_mod.educational(producer_path)
