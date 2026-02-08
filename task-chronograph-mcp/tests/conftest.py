"""Shared test fixtures for Task Chronograph tests."""

from __future__ import annotations

import asyncio

import pytest

from task_chronograph_mcp.events import (
    AgentStatus,
    Event,
    EventStore,
    EventType,
    Interaction,
)


@pytest.fixture
async def event_store() -> EventStore:
    """Fresh EventStore with the test's event loop registered for broadcasting."""
    store = EventStore()
    store.set_loop(asyncio.get_running_loop())
    return store


@pytest.fixture
def sample_event_payload() -> dict:
    """Valid payload for POST /api/events (agent_start)."""
    return {
        "event_type": "agent_start",
        "agent_type": "researcher",
        "session_id": "sess-001",
        "agent_id": "agent-001",
        "parent_session_id": "parent-001",
        "message": "Agent researcher started",
        "labels": {"feature": "auth"},
    }


@pytest.fixture
def sample_event() -> Event:
    """Pre-built Event instance for unit tests."""
    return Event(
        event_type=EventType.AGENT_START,
        agent_type="researcher",
        session_id="sess-001",
        agent_id="agent-001",
        parent_session_id="parent-001",
        message="Agent researcher started",
        labels={"feature": "auth"},
    )


@pytest.fixture
def sample_interaction() -> Interaction:
    """Pre-built Interaction instance for unit tests."""
    return Interaction(
        source="main_agent",
        target="researcher",
        summary="Delegate research on auth options",
        interaction_type="delegation",
        labels={"priority": "high"},
    )


@pytest.fixture
def phase_event() -> Event:
    """Pre-built phase_transition Event for unit tests."""
    return Event(
        event_type=EventType.PHASE_TRANSITION,
        agent_type="researcher",
        agent_id="agent-001",
        phase=2,
        total_phases=5,
        phase_name="analysis",
        message="Analyzing auth libraries",
        labels={"feature": "auth"},
        status=AgentStatus.RUNNING,
    )
