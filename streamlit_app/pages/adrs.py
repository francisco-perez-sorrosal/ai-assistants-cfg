"""ADRs browser — finalized + draft architecture decision records."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from streamlit_app.config import get_config
from streamlit_app.data import cache, discovery
from streamlit_app.widgets import artifact_card, empty_state, graph as graphw

# Path to the ADR conventions rule file relative to a Praxion project root.
_ADR_CONVENTIONS_REL = "rules/swe/adr-conventions.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_adr(path: Path, is_draft: bool) -> dict:
    """Return a parsed ADR dict with frontmatter, body, path, and is_draft."""
    try:
        fm, body = cache.cached_parse_frontmatter(str(path), cache.mtime_of(path))
    except Exception:  # noqa: BLE001 — degrade on any unreadable file
        fm, body = {}, ""
    return {"path": path, "frontmatter": fm, "body": body, "is_draft": is_draft}


def _build_filter_sets(all_adrs: list[dict]) -> tuple[list[str], list[str], list[str]]:
    """Return sorted (statuses, categories, all_tags) from parsed ADR list."""
    statuses = sorted({a["frontmatter"].get("status", "") for a in all_adrs} - {""})
    categories = sorted({a["frontmatter"].get("category", "") for a in all_adrs} - {""})
    all_tags = sorted(
        {t for a in all_adrs for t in (a["frontmatter"].get("tags") or [])}
    )
    return statuses, categories, all_tags


def _apply_filters(
    all_adrs: list[dict],
    selected_statuses: list[str],
    selected_categories: list[str],
    selected_tags: list[str],
) -> list[dict]:
    """Return ADRs matching the selected filter values."""
    result = []
    for adr in all_adrs:
        fm = adr["frontmatter"]
        if selected_statuses and fm.get("status", "") not in selected_statuses:
            continue
        if selected_categories and fm.get("category", "") not in selected_categories:
            continue
        if selected_tags and not (set(selected_tags) & set(fm.get("tags") or [])):
            continue
        result.append(adr)
    return result


def _render_lineage(visible: list[dict]) -> None:
    """Render supersession lineage DAG if any visible ADR has edges."""
    has_edges = any(
        a["frontmatter"].get("supersedes") or a["frontmatter"].get("superseded_by")
        for a in visible
    )
    if not has_edges:
        return

    adr_dicts = [
        {
            "id": a["frontmatter"].get("id", a["path"].stem),
            "title": a["frontmatter"].get("title", a["path"].name),
            "status": a["frontmatter"].get("status", "unknown"),
            "supersedes": a["frontmatter"].get("supersedes"),
            "superseded_by": a["frontmatter"].get("superseded_by"),
        }
        for a in visible
    ]
    with st.expander(
        f"Supersession lineage ({len(visible)} ADRs visible)", expanded=False
    ):
        st.graphviz_chart(graphw.adr_lineage_dot(adr_dicts), use_container_width=True)


def _render_cards(visible: list[dict], conventions_path: str) -> None:
    """Render one artifact_card per visible ADR."""
    draft_count = sum(1 for a in visible if a["is_draft"])
    finalized_count = len(visible) - draft_count
    st.markdown(
        f"**{len(visible)}** ADRs match filters"
        f" ({draft_count} drafts, {finalized_count} finalized)."
    )
    for adr in visible:
        title = adr["frontmatter"].get("title", adr["path"].name)
        if adr["is_draft"]:
            title = f"[draft] {title}"
        artifact_card.artifact_card(
            title=title,
            body_md=adr["body"],
            metadata=adr["frontmatter"],
            what_is_this=conventions_path,
            expanded=False,
        )


# ---------------------------------------------------------------------------
# Page entry point
# ---------------------------------------------------------------------------


def render() -> None:
    """Render the ADRs page."""
    config = get_config()
    finalized = discovery.list_adrs_finalized(config.project_root)
    drafts = discovery.list_adrs_drafts(config.project_root)

    st.title("Architecture Decision Records")
    st.caption(
        "Finalized ADRs (`<NNN>-<slug>.md`) plus pipeline drafts (`drafts/*.md`)."
        " Decisions are immutable; supersession is the only edit."
    )

    conventions_path = str(config.project_root / _ADR_CONVENTIONS_REL)

    if not finalized and not drafts:
        empty_state.empty_state(
            artifact_name="Architecture Decision Records",
            producer_path=conventions_path,
            explanation=(
                "No ADRs found in this project. ADRs are produced by"
                " `systems-architect` and `implementation-planner` during pipelines"
                " and finalized at merge-to-main."
            ),
        )
        return

    all_adrs = [_parse_adr(p, is_draft=False) for p in finalized]
    all_adrs += [_parse_adr(p, is_draft=True) for p in drafts]

    statuses, categories, all_tags = _build_filter_sets(all_adrs)

    selected_statuses = st.sidebar.multiselect("Status", statuses, default=statuses)
    selected_categories = st.sidebar.multiselect(
        "Category", categories, default=categories
    )
    selected_tags = st.sidebar.multiselect("Tags (any)", all_tags, default=[])

    visible = _apply_filters(
        all_adrs, selected_statuses, selected_categories, selected_tags
    )

    _render_lineage(visible)
    _render_cards(visible, conventions_path)
