"""Tests for the Starlette server: HTTP API, SSE, dashboard, and MCP tools."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from task_chronograph_mcp.events import EventStore, Interaction
from task_chronograph_mcp.server import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_URL = "http://test"


@pytest.fixture
async def client():
    """Async HTTP client with ASGI transport and lifespan properly managed.

    httpx.ASGITransport does not run Starlette lifespan events, so we
    manually enter the app lifespan context before creating the client.
    """
    import task_chronograph_mcp.server as server_module

    # Manually run lifespan to initialize store
    async with server_module.app_lifespan(app):
        transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]
        async with httpx.AsyncClient(transport=transport, base_url=BASE_URL) as c:
            yield c


# ---------------------------------------------------------------------------
# POST /api/events
# ---------------------------------------------------------------------------


class TestReceiveEvent:
    async def test_valid_payload_returns_201(
        self, client: httpx.AsyncClient, sample_event_payload: dict
    ):
        resp = await client.post("/api/events", json=sample_event_payload)
        assert resp.status_code == 201
        body = resp.json()
        assert "event_id" in body

    async def test_missing_required_fields_returns_400(self, client: httpx.AsyncClient):
        resp = await client.post("/api/events", json={"agent_type": "researcher"})
        assert resp.status_code == 400
        assert "event_type" in resp.json()["error"]

    async def test_invalid_event_type_returns_400(self, client: httpx.AsyncClient):
        resp = await client.post(
            "/api/events",
            json={"event_type": "not_real", "agent_type": "researcher"},
        )
        assert resp.status_code == 400
        assert "Invalid event_type" in resp.json()["error"]

    async def test_invalid_json_returns_400(self, client: httpx.AsyncClient):
        resp = await client.post(
            "/api/events",
            content=b"not json",
            headers={"content-type": "application/json"},
        )
        assert resp.status_code == 400
        assert "Invalid JSON" in resp.json()["error"]


# ---------------------------------------------------------------------------
# GET /api/state
# ---------------------------------------------------------------------------


class TestPipelineState:
    async def test_empty_state_structure(self, client: httpx.AsyncClient):
        resp = await client.get("/api/state")
        assert resp.status_code == 200
        body = resp.json()
        assert "agents" in body
        assert "interactions" in body
        assert "delegation_chain" in body
        assert "event_count" in body
        assert "recent_events" in body

    async def test_state_reflects_posted_event(
        self, client: httpx.AsyncClient, sample_event_payload: dict
    ):
        await client.post("/api/events", json=sample_event_payload)
        resp = await client.get("/api/state")
        body = resp.json()
        assert body["event_count"] == 1
        assert len(body["agents"]) == 1

    async def test_state_includes_stopped_at_after_stop(
        self, client: httpx.AsyncClient, sample_event_payload: dict
    ):
        await client.post("/api/events", json=sample_event_payload)
        await client.post(
            "/api/events",
            json={
                "event_type": "agent_stop",
                "agent_type": "researcher",
                "agent_id": "agent-001",
            },
        )
        resp = await client.get("/api/state")
        agent = resp.json()["agents"]["agent-001"]
        assert agent["stopped_at"] is not None
        assert agent["status"] == "complete"

    async def test_state_includes_task_summary_from_delegation(
        self, client: httpx.AsyncClient
    ):
        import task_chronograph_mcp.server as server_module

        store: EventStore = server_module._store  # type: ignore[assignment]
        delegation = Interaction(
            source="main_agent",
            target="researcher",
            summary="Research auth patterns",
            interaction_type="delegation",
        )
        await store.add_interaction(delegation)

        await client.post(
            "/api/events",
            json={
                "event_type": "agent_start",
                "agent_type": "researcher",
                "agent_id": "researcher",
            },
        )

        resp = await client.get("/api/state")
        agent = resp.json()["agents"]["researcher"]
        assert agent["task_summary"] == "Research auth patterns"


# ---------------------------------------------------------------------------
# GET /api/events/stream (SSE)
# ---------------------------------------------------------------------------


class TestSSEStream:
    async def test_sse_subscribe_and_broadcast_integration(self, client: httpx.AsyncClient):
        """Verify that the EventStore used by the server supports SSE pub/sub.

        Full SSE HTTP streaming cannot be tested with httpx ASGITransport because
        the EventSourceResponse keeps the connection open indefinitely, blocking
        the single-threaded ASGI transport. Instead, we test the pub/sub mechanism
        that backs the SSE endpoint directly via the server's store.
        The subscribe/unsubscribe unit tests are in test_events.py; this test
        verifies the server's store instance is wired correctly.
        """
        import task_chronograph_mcp.server as server_module
        from task_chronograph_mcp.events import Event, EventType

        store: EventStore = server_module._store  # type: ignore[assignment]

        queue = store.subscribe()
        event = Event(event_type=EventType.AGENT_START, agent_type="researcher")
        await store.add(event)

        received = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert received.agent_type == "researcher"
        assert received.event_type == EventType.AGENT_START

        store.unsubscribe(queue)


# ---------------------------------------------------------------------------
# GET / (Dashboard)
# ---------------------------------------------------------------------------


class TestDashboard:
    async def test_dashboard_returns_html(self, client: httpx.AsyncClient):
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    async def test_dashboard_contains_title(self, client: httpx.AsyncClient):
        resp = await client.get("/")
        assert "Task Chronograph" in resp.text

    async def test_dashboard_hydrated_with_agent_data(
        self, client: httpx.AsyncClient, sample_event_payload: dict
    ):
        """Post events, then GET / and verify the agent appears in the HTML."""
        await client.post("/api/events", json=sample_event_payload)
        resp = await client.get("/")
        assert "researcher" in resp.text

    async def test_dashboard_shows_task_summary(
        self, client: httpx.AsyncClient, sample_event_payload: dict
    ):
        """Agent card shows task_summary from delegation interaction."""
        import task_chronograph_mcp.server as server_module

        store: EventStore = server_module._store  # type: ignore[assignment]
        delegation = Interaction(
            source="main_agent",
            target="agent-001",
            summary="Research auth patterns",
            interaction_type="delegation",
        )
        await store.add_interaction(delegation)
        await client.post("/api/events", json=sample_event_payload)

        resp = await client.get("/")
        assert "Research auth patterns" in resp.text

    async def test_dashboard_shows_elapsed_time(
        self, client: httpx.AsyncClient, sample_event_payload: dict
    ):
        """Agent card shows elapsed duration for running agents."""
        await client.post("/api/events", json=sample_event_payload)
        resp = await client.get("/")
        assert "Started" in resp.text

    async def test_dashboard_shows_interaction_timeline(self, client: httpx.AsyncClient):
        """Add an interaction via the store, verify it appears in dashboard."""
        import task_chronograph_mcp.server as server_module

        store: EventStore = server_module._store  # type: ignore[assignment]
        interaction = Interaction(
            source="main_agent",
            target="researcher",
            summary="Delegate auth research",
            interaction_type="delegation",
        )
        await store.add_interaction(interaction)

        resp = await client.get("/")
        assert "Delegate auth research" in resp.text


# ---------------------------------------------------------------------------
# MCP tool: report_interaction (tested directly via store)
# ---------------------------------------------------------------------------


class TestMCPReportInteraction:
    async def test_report_interaction_delegation_creates_hierarchy(self, client: httpx.AsyncClient):
        """Use store directly to simulate report_interaction tool behavior."""
        import task_chronograph_mcp.server as server_module

        store: EventStore = server_module._store  # type: ignore[assignment]

        interaction = Interaction(
            source="main_agent",
            target="researcher",
            summary="Delegate research",
            interaction_type="delegation",
        )
        await store.add_interaction(interaction)

        # Now start both agents via API
        await client.post(
            "/api/events",
            json={
                "event_type": "agent_start",
                "agent_type": "main_agent",
                "agent_id": "main_agent",
            },
        )
        await client.post(
            "/api/events",
            json={
                "event_type": "agent_start",
                "agent_type": "researcher",
                "agent_id": "researcher",
            },
        )

        resp = await client.get("/api/state")
        state = resp.json()
        assert state["agents"]["researcher"]["delegation_parent"] == "main_agent"
        assert len(state["delegation_chain"]) == 1

    async def test_report_interaction_unknown_type_accepted(self, client: httpx.AsyncClient):
        """Unknown interaction type is stored and returned in API."""
        import task_chronograph_mcp.server as server_module

        store: EventStore = server_module._store  # type: ignore[assignment]

        interaction = Interaction(
            source="a", target="b", summary="custom action", interaction_type="novel_kind"
        )
        await store.add_interaction(interaction)

        resp = await client.get("/api/state")
        state = resp.json()
        assert len(state["interactions"]) == 1
        assert state["interactions"][0]["interaction_type"] == "novel_kind"
