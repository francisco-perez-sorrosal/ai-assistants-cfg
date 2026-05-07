"""Workshops page — live supervision of in-flight pipelines (.ai-work/<task-slug>/)."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — used at runtime in _render_workshop params

import streamlit as st

from streamlit_app.config import get_config
from streamlit_app.data import cache, discovery
from streamlit_app.widgets import educational, empty_state
from streamlit_app.widgets import graph as graphw

# Canonical workshop artifact filenames (agent-intermediate-documents rule).
_CANONICAL_ARTIFACTS = [
    "SYSTEMS_PLAN.md",
    "IMPLEMENTATION_PLAN.md",
    "WIP.md",
    "LEARNINGS.md",
    "TEST_RESULTS.md",
    "traceability.yml",
    "VERIFICATION_REPORT.md",
    "PROGRESS.md",
    "RESEARCH_FINDINGS.md",
    "IDEA_PROPOSAL.md",
    "CONTEXT_REVIEW.md",
    "SPEC_DELTA.md",
    "SKILL_GENESIS_REPORT.md",
]

# Minimum step count before rendering the step DAG.
_DAG_MIN_STEPS = 3

# Maximum phase-transition events shown in the log expander.
_MAX_LOG_EVENTS = 10


def render() -> None:
    """Single-callable page entry — live supervision of in-flight pipelines.

    Reads PRAXION_PROJECT_ROOT, lists active workshops, renders each via a
    fragment for live refresh. Empty state when none exist (transient by design).
    """
    config = get_config()
    workshops = discovery.list_active_workshops(config.project_root)

    st.title("Workshops")
    st.caption(
        "Live view of in-flight pipelines — `.ai-work/<task-slug>/` directories."
    )

    if not workshops:
        empty_state.empty_state(
            artifact_name="Active workshops",
            producer_path=str(
                config.project_root
                / "rules"
                / "swe"
                / "swe-agent-coordination-protocol.md"
            ),
            explanation=(
                "No `.ai-work/<task-slug>/` directories found. "
                "Workshops appear here while a pipeline is in flight; "
                "they are deleted at pipeline cleanup (transient by design)."
            ),
        )
        return

    for workshop_dir in workshops:
        _render_workshop(workshop_dir)


@st.fragment(run_every=15)
def _render_workshop(workshop_dir: Path) -> None:
    """Render one workshop's live state. Auto-refreshes every 15 s.

    Sections:
      1. Header: task slug + current step + status
      2. WIP progress: phase-grouped checklist in an expander
      3. Step DAG: graphviz chart of progress items when enough steps present
      4. Phase-transition log: last several entries from PROGRESS.md
      5. Artifacts: canonical artifacts present in this workshop directory
    """
    st.subheader(workshop_dir.name)

    _render_wip_section(workshop_dir)
    _render_progress_log_section(workshop_dir)
    _render_artifacts_section(workshop_dir)
    st.divider()


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------


def _render_wip_section(workshop_dir: Path) -> None:
    """Render WIP.md content: current step, status, progress checklist, DAG."""
    wip_path = discovery.find_workshop_artifact(workshop_dir, "WIP.md")
    if not wip_path:
        st.info("No `WIP.md` found in this workshop yet.")
        return

    wip = cache.cached_parse_wip(str(wip_path), cache.mtime_of(wip_path))

    current_step = wip.get("current_step") or "—"
    status = wip.get("status") or "—"

    col_step, col_status = st.columns(2)
    with col_step:
        st.markdown(f"**Current step:** {current_step}")
    with col_status:
        st.markdown(f"**Status:** {status}")

    progress_items = wip.get("progress") or []
    if progress_items:
        _render_progress_checklist(progress_items)
        if len(progress_items) >= _DAG_MIN_STEPS:
            _render_step_dag(progress_items)


def _render_progress_checklist(progress_items: list[dict]) -> None:
    """Render the WIP progress list as a collapsible checklist."""
    done_count = sum(1 for p in progress_items if p.get("done"))
    total = len(progress_items)

    with st.expander(f"Progress ({done_count}/{total} done)", expanded=False):
        for item in progress_items:
            icon = "✅" if item.get("done") else "⬜"
            step_id = item.get("step_id") or "?"
            label = item.get("label") or ""
            st.markdown(f"{icon} **{step_id}**: {label}")


def _render_step_dag(progress_items: list[dict]) -> None:
    """Render the step DAG via graphviz when enough nodes exist."""
    step_nodes = [
        {
            "step_id": p.get("step_id", ""),
            "label": p.get("label", ""),
            "done": bool(p.get("done", False)),
            "dependencies": [],
        }
        for p in progress_items
        if p.get("step_id")
    ]
    if len(step_nodes) < _DAG_MIN_STEPS:
        return

    dot = graphw.step_dag_dot(step_nodes)
    with st.expander("Step DAG", expanded=False):
        st.graphviz_chart(dot, use_container_width=True)


def _render_progress_log_section(workshop_dir: Path) -> None:
    """Render the phase-transition log from PROGRESS.md."""
    progress_path = discovery.find_workshop_artifact(workshop_dir, "PROGRESS.md")
    if not progress_path:
        return

    events = cache.cached_parse_progress(
        str(progress_path), cache.mtime_of(progress_path)
    )
    if not events:
        return

    recent = events[-_MAX_LOG_EVENTS:]
    with st.expander(f"Phase-transition log ({len(events)} events)", expanded=False):
        for ev in recent:
            timestamp = ev.get("timestamp", "")
            agent = ev.get("agent", "?")
            phase = ev.get("phase", "?")
            summary = ev.get("summary", "")
            st.markdown(f"- `{timestamp}` **{agent}** Phase `{phase}` — {summary}")


def _render_artifacts_section(workshop_dir: Path) -> None:
    """List canonical artifacts present in this workshop directory."""
    present = [
        name
        for name in _CANONICAL_ARTIFACTS
        if discovery.find_workshop_artifact(workshop_dir, name)
    ]
    if not present:
        return

    with st.expander(f"Artifacts ({len(present)} present)", expanded=False):
        for name in present:
            st.markdown(f"- `{name}`")

    educational.educational_popover(
        str(
            get_config().project_root
            / "rules"
            / "swe"
            / "agent-intermediate-documents.md"
        )
    )
