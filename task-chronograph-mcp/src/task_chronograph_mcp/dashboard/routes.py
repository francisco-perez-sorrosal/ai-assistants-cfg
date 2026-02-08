"""Dashboard HTTP routes and Jinja2 template rendering."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from starlette.requests import Request
from starlette.responses import HTMLResponse

from task_chronograph_mcp.events import EventStore

TEMPLATES_DIR = Path(__file__).parent / "templates"

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)


def _build_agent_hierarchy(agents: dict) -> tuple[list[str], dict[str, list[str]]]:
    """Separate root agents from children and build a children map.

    Returns (root_agent_keys, children_map) where root agents have no
    delegation_parent, and children_map maps parent_key -> [child_keys].
    """
    children_map: dict[str, list[str]] = {}
    root_agents: list[str] = []

    for key, agent in agents.items():
        parent = agent.get("delegation_parent", "")
        if parent:
            children_map.setdefault(parent, []).append(key)
        else:
            root_agents.append(key)

    return root_agents, children_map


def _format_interaction_timestamps(interactions: list[dict]) -> list[dict]:
    """Add a display-friendly timestamp field to each interaction dict."""
    formatted = []
    for interaction in interactions:
        enriched = dict(interaction)
        raw_ts = interaction.get("timestamp", "")
        enriched["timestamp_display"] = _format_timestamp(raw_ts)
        formatted.append(enriched)
    return formatted


def _format_timestamp(iso_timestamp: str) -> str:
    """Extract HH:MM:SS from an ISO timestamp for compact display."""
    if not iso_timestamp:
        return ""
    # ISO format: 2025-01-15T14:30:00.123456+00:00
    # Extract the time portion after 'T'
    if "T" in iso_timestamp:
        time_part = iso_timestamp.split("T")[1]
        # Take HH:MM:SS, dropping fractional seconds and timezone
        return time_part[:8]
    return iso_timestamp


def _format_elapsed(seconds: float) -> str:
    """Format a duration in seconds as a human-readable string (e.g. '2m 15s')."""
    total = int(seconds)
    if total < 60:
        return f"{total}s"
    minutes, secs = divmod(total, 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m"


def _format_agent_timestamps(agents: dict, now: datetime | None = None) -> dict:
    """Enrich each agent dict with display-friendly timing fields.

    Adds: started_at_display, stopped_at_display, elapsed_display.
    """
    now = now or datetime.now(UTC)
    enriched = {}
    for key, agent in agents.items():
        agent = dict(agent)
        agent["started_at_display"] = _format_timestamp(agent.get("started_at") or "")
        agent["stopped_at_display"] = _format_timestamp(agent.get("stopped_at") or "")

        started_iso = agent.get("started_at")
        stopped_iso = agent.get("stopped_at")
        if started_iso:
            started = datetime.fromisoformat(started_iso)
            end = datetime.fromisoformat(stopped_iso) if stopped_iso else now
            elapsed_seconds = (end - started).total_seconds()
            agent["elapsed_display"] = _format_elapsed(elapsed_seconds)
        else:
            agent["elapsed_display"] = ""

        enriched[key] = agent
    return enriched


async def dashboard_handler(request: Request) -> HTMLResponse:
    """GET / -- render the main dashboard with initial state hydration."""
    store: EventStore = request.app.state.store
    state = store.get_pipeline_summary()

    state["agents"] = _format_agent_timestamps(state["agents"])
    root_agents, children_map = _build_agent_hierarchy(state["agents"])
    state["interactions"] = _format_interaction_timestamps(state["interactions"])

    template = _jinja_env.get_template("dashboard.html")
    html = template.render(
        state=state,
        root_agents=root_agents,
        children_map=children_map,
    )
    return HTMLResponse(html)
