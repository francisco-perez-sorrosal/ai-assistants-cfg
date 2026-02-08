"""Starlette application with MCP server, HTTP API, and dashboard routes."""

from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from sse_starlette.sse import EventSourceResponse
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from task_chronograph_mcp.dashboard.routes import dashboard_handler
from task_chronograph_mcp.events import (
    AgentStatus,
    Event,
    EventStore,
    EventType,
    Interaction,
)
from task_chronograph_mcp.file_watcher import watch_progress_file

DEFAULT_PORT = 8765
WATCH_DIR_ENV = "CHRONOGRAPH_WATCH_DIR"

mcp = FastMCP("Task Chronograph")
_store: EventStore | None = None


@asynccontextmanager
async def app_lifespan(app: Starlette):
    global _store  # noqa: PLW0603
    _store = EventStore()
    app.state.store = _store

    watch_dir = os.environ.get(WATCH_DIR_ENV, "")
    watcher_task: asyncio.Task | None = None
    if watch_dir:
        watch_path = Path(watch_dir)
        watcher_task = asyncio.create_task(watch_progress_file(watch_path, app.state.store))

    yield

    if watcher_task is not None:
        watcher_task.cancel()
        try:
            await watcher_task
        except asyncio.CancelledError:
            pass


async def receive_event(request: Request) -> JSONResponse:
    """POST /api/events -- ingest a pipeline event."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    missing = [f for f in ("event_type", "agent_type") if f not in body]
    if missing:
        return JSONResponse(
            {"error": f"Missing required fields: {', '.join(missing)}"},
            status_code=400,
        )

    try:
        event_type = EventType(body["event_type"])
    except ValueError:
        valid = [e.value for e in EventType]
        return JSONResponse(
            {"error": f"Invalid event_type: {body['event_type']}. Valid types: {valid}"},
            status_code=400,
        )

    event = Event(
        event_type=event_type,
        agent_type=body["agent_type"],
        session_id=body.get("session_id", ""),
        agent_id=body.get("agent_id", ""),
        parent_session_id=body.get("parent_session_id", ""),
        phase=body.get("phase", 0),
        total_phases=body.get("total_phases", 0),
        phase_name=body.get("phase_name", ""),
        status=AgentStatus(body.get("status", "running")),
        message=body.get("message", ""),
        labels=body.get("labels", {}),
        metadata=body.get("metadata", {}),
    )

    store: EventStore = request.app.state.store
    await store.add(event)

    return JSONResponse({"event_id": event.event_id}, status_code=201)


async def pipeline_state(request: Request) -> JSONResponse:
    """GET /api/state -- return full pipeline summary."""
    store: EventStore = request.app.state.store
    return JSONResponse(store.get_pipeline_summary())


async def sse_stream(request: Request) -> EventSourceResponse:
    """GET /api/events/stream -- SSE endpoint for real-time event delivery."""
    store: EventStore = request.app.state.store
    queue = store.subscribe()

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                event = await queue.get()
                event_type_value = (
                    event.event_type.value
                    if isinstance(event.event_type, EventType)
                    else str(event.event_type)
                )
                yield {
                    "event": event_type_value,
                    "data": json.dumps(event.to_dict()),
                }
        finally:
            store.unsubscribe(queue)

    return EventSourceResponse(event_generator())


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def get_pipeline_status() -> dict:
    """Get current status of all agents in the pipeline.

    Returns a summary of each agent's state including current phase,
    status (running/complete/failed), labels, delegation hierarchy,
    interaction timeline, and delegation chain.
    """
    if _store is None:
        return {"error": "Store not initialized"}
    return _store.get_pipeline_summary()


@mcp.tool()
def get_agent_events(agent_type: str, limit: int = 20, label: str = "") -> list[dict]:
    """Get recent events for a specific agent type.

    Args:
        agent_type: The agent type to query (e.g., "researcher", "systems-architect").
        limit: Maximum number of events to return (default 20).
        label: Optional label filter (e.g., "feature=auth"). Only events with matching label returned.
    """
    if _store is None:
        return []
    return _store.get_events_by_agent(agent_type, limit, label or None)


@mcp.tool()
async def report_interaction(
    source: str,
    target: str,
    summary: str,
    interaction_type: str,
    labels: dict[str, str] | None = None,
) -> dict:
    """Record an interaction between pipeline participants.

    Call at key moments to build the interaction timeline:
    - "query": User asks the main agent something
    - "delegation": Main agent delegates to a subagent
    - "result": Agent returns findings to main agent
    - "decision": Main agent makes a pipeline routing decision
    - "response": Main agent responds to the user

    Delegation interactions implicitly create hierarchy links.
    Unknown types are accepted with a generic badge.

    Args:
        source: Who initiated (e.g., "user", "main_agent", "researcher").
        target: Who receives (e.g., "main_agent", "researcher", "user").
        summary: One-sentence description of what happened.
        interaction_type: One of "query", "delegation", "result", "decision", "response" (extensible).
        labels: Optional key-value annotations.
    """
    if _store is None:
        return {"error": "Store not initialized"}
    interaction = Interaction(
        source=source,
        target=target,
        summary=summary,
        interaction_type=interaction_type,
        labels=labels or {},
    )
    interaction_id = await _store.add_interaction(interaction)
    return {"status": "recorded", "interaction_id": interaction_id}


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = Starlette(
    routes=[
        Route("/", dashboard_handler, methods=["GET"]),
        Route("/api/events", receive_event, methods=["POST"]),
        Route("/api/state", pipeline_state, methods=["GET"]),
        Route("/api/events/stream", sse_stream, methods=["GET"]),
        Mount("/mcp", mcp.streamable_http_app()),
    ],
    lifespan=app_lifespan,
)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("CHRONOGRAPH_PORT", str(DEFAULT_PORT)))
    uvicorn.run(app, host="0.0.0.0", port=port)
