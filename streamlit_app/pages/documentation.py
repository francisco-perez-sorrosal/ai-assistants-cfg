"""Documentation page — manifest-driven navigation across all doc surfaces.

Reads `.ai-state/doc_manifest.yaml` (produced by `scripts/build_doc_manifest.py`)
and dispatches the user-selected surface through the component library
(`streamlit_app.components.dispatch`).

Per `rules/writing/html-output-conventions.md`:
- MD is read live (never pre-baked)
- HTML rendering happens here in Streamlit, not as committed `.html`
- Components are typed by Diátaxis quadrant + filename pattern
- No JavaScript in the rendered output (declarative HTML only)

Per `rules/swe/dashboard-conventions.md`:
- Empty-state degrades gracefully when manifest is absent
- mtime-keyed caching for the manifest load (cached_parse_yaml does this)
- Single `render()` entry; no module-level Streamlit calls
"""

from __future__ import annotations

import streamlit as st

from streamlit_app import config
from streamlit_app.components import dispatch
from streamlit_app.data.cache import cached_parse_yaml, mtime_of
from streamlit_app.widgets.empty_state import empty_state


def _format_surface_label(surface: dict) -> str:
    """Format a surface for display in the sidebar select."""
    title = surface.get("title", surface["id"])
    diataxis = surface.get("diataxis", "")
    diataxis_chip = f" [{diataxis}]" if diataxis else ""
    return f"{title}{diataxis_chip}"


def render() -> None:
    cfg = config.get_config()
    project_root = cfg.project_root
    manifest_path = project_root / ".ai-state" / "doc_manifest.yaml"

    if not manifest_path.is_file():
        st.header("📚 Documentation")
        empty_state(
            "doc_manifest.yaml",
            producer_path="scripts/build_doc_manifest.py",
            explanation=(
                "No **doc_manifest.yaml** found in this project."
                " The Documentation page reads it to discover and dispatch every"
                " doc surface (markdown, YAML, JSON, SVG) through the component"
                " library."
                "\n\n**To generate it**, run:"
                "\n\n    python3 scripts/build_doc_manifest.py"
                "\n\nThe manifest regenerates deterministically from the filesystem;"
                " a post-commit hook can keep it fresh automatically."
            ),
        )
        return

    manifest = cached_parse_yaml(str(manifest_path), mtime_of(manifest_path))
    if not isinstance(manifest, dict) or "surfaces" not in manifest:
        st.error(
            f"`{manifest_path.relative_to(project_root)}` is malformed."
            " Re-run `python3 scripts/build_doc_manifest.py`."
        )
        return

    surfaces: list[dict] = manifest.get("surfaces") or []
    groups: list[dict] = manifest.get("groups") or []
    surfaces_by_id = {s["id"]: s for s in surfaces}

    # ── Header ────────────────────────────────────────────────────────────
    st.header("📚 Documentation")
    st.caption(
        f"{len(surfaces)} surfaces across {len(groups)} groups · "
        f"manifest generated `{manifest.get('generated_at', 'unknown')}`"
    )

    # ── Sidebar: group → surface select ──────────────────────────────────
    with st.sidebar:
        st.markdown("**Documentation surfaces**")

        if not groups:
            st.caption("(No groups defined in manifest.)")
            return

        group_choices = {g["id"]: g for g in groups}
        group_labels = {
            gid: f"{g['label']} ({len(g['surface_ids'])})"
            for gid, g in group_choices.items()
        }

        # Default to first non-transient group for cold-start; transient groups
        # have unstable contents and shouldn't anchor navigation.
        default_idx = next(
            (i for i, g in enumerate(groups) if not g.get("transient")), 0
        )

        selected_group_id = st.selectbox(
            "Group",
            options=list(group_choices.keys()),
            format_func=lambda gid: group_labels[gid],
            index=default_idx,
            key="documentation_group",
        )

        selected_group = group_choices[selected_group_id]
        if selected_group.get("transient"):
            st.caption("⏳ *Transient — disappears when no active pipeline.*")

        surface_ids = selected_group.get("surface_ids") or []
        if not surface_ids:
            st.caption("(No surfaces in this group.)")
            return

        # Filter to surfaces actually in the manifest (defensive)
        valid_surfaces = [
            surfaces_by_id[sid] for sid in surface_ids if sid in surfaces_by_id
        ]
        if not valid_surfaces:
            st.warning("Group lists surface ids not found in manifest.")
            return

        selected_surface_id = st.radio(
            "Surface",
            options=[s["id"] for s in valid_surfaces],
            format_func=lambda sid: _format_surface_label(surfaces_by_id[sid]),
            key=f"documentation_surface_{selected_group_id}",
        )

    # ── Main area: dispatch through the component library ──────────────
    selected_surface = surfaces_by_id.get(selected_surface_id)
    if not selected_surface:
        st.error("Selected surface not found in manifest.")
        return

    dispatch(selected_surface, project_root)
