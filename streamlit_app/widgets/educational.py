"""Educational widget — every artifact has a "What is this?" affordance
linking to the producer skill/rule/agent."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from streamlit_app.data import parsers


def resolve_description(target_path: Path | str) -> str:
    """Return a one-line description for the given target path.

    Reads frontmatter ``description:`` if present.
    Falls back to the first non-empty paragraph of the body.
    Falls back to "Description not available." for missing/unreadable files.

    PURE: no Streamlit calls — testable in isolation.
    """
    path = Path(target_path)
    try:
        metadata, body = parsers.parse_frontmatter(path)
    except FileNotFoundError:
        return "Description not available."
    except Exception:  # noqa: BLE001 — degrade on any unreadable file
        return "Description not available."

    if metadata.get("description"):
        return str(metadata["description"])

    # Fall back to first non-empty paragraph of the body.
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped

    return "Description not available."


def educational(
    target_path: str,
    label: str = "What is this?",
    use_popover: bool = True,
) -> None:
    """Render the educational affordance.

    Args:
        target_path: path string to a skill/rule/agent file (relative to
            PROJECT_ROOT or absolute). Resolved via Path; if it does not exist,
            falls back to "Description not available."
        label: button/expander label.
        use_popover: if True (default), use st.popover; else st.expander.
    """
    resolved = Path(target_path)
    description = resolve_description(resolved)
    filename = resolved.name
    content = f"**{filename}**\n\n{description}\n\n[Open file](file://{target_path})"

    if use_popover:
        with st.popover(label):
            st.markdown(content)
    else:
        with st.expander(label):
            st.markdown(content)


def educational_popover(skill_path: str) -> None:
    """Render a 'What is this?' educational popover.

    Strips any ``#anchor`` fragment from ``skill_path`` before reading the
    file — the anchor is for display context only, not file addressing.

    Degrades gracefully when the path does not exist.
    """
    # Strip any #anchor fragment before resolving the file.
    clean_path, _, _ = skill_path.partition("#")
    educational(clean_path.strip(), use_popover=False)
