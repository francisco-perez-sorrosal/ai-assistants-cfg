"""Tests for Event model, Interaction model, and EventStore."""

from __future__ import annotations

import asyncio
from datetime import datetime

from task_chronograph_mcp.events import (
    AgentStatus,
    Event,
    EventStore,
    EventType,
    Interaction,
)

# ---------------------------------------------------------------------------
# Event model
# ---------------------------------------------------------------------------


class TestEventCreation:
    def test_event_has_required_fields(self, sample_event: Event):
        assert sample_event.event_type == EventType.AGENT_START
        assert sample_event.agent_type == "researcher"
        assert sample_event.session_id == "sess-001"
        assert sample_event.agent_id == "agent-001"

    def test_event_defaults(self):
        event = Event(event_type=EventType.AGENT_START, agent_type="researcher")
        assert event.event_id != ""
        assert isinstance(event.timestamp, datetime)
        assert event.labels == {}
        assert event.metadata == {}
        assert event.status == AgentStatus.RUNNING

    def test_event_is_frozen(self, sample_event: Event):
        try:
            sample_event.agent_type = "other"  # type: ignore[misc]
            raise AssertionError("Expected FrozenInstanceError")
        except AttributeError:
            pass


class TestEventSerialization:
    def test_to_dict_contains_all_fields(self, sample_event: Event):
        d = sample_event.to_dict()
        assert d["event_type"] == "agent_start"
        assert d["agent_type"] == "researcher"
        assert d["session_id"] == "sess-001"
        assert d["status"] == "running"
        assert d["labels"] == {"feature": "auth"}
        assert isinstance(d["timestamp"], str)

    def test_to_dict_enum_values_are_strings(self, sample_event: Event):
        d = sample_event.to_dict()
        assert isinstance(d["event_type"], str)
        assert isinstance(d["status"], str)


# ---------------------------------------------------------------------------
# Interaction model
# ---------------------------------------------------------------------------


class TestInteractionCreation:
    def test_interaction_has_required_fields(self, sample_interaction: Interaction):
        assert sample_interaction.source == "main_agent"
        assert sample_interaction.target == "researcher"
        assert sample_interaction.interaction_type == "delegation"
        assert sample_interaction.summary == "Delegate research on auth options"

    def test_interaction_defaults(self):
        interaction = Interaction(
            source="user", target="main_agent", summary="Ask about auth", interaction_type="query"
        )
        assert interaction.interaction_id != ""
        assert isinstance(interaction.timestamp, datetime)
        assert interaction.labels == {}

    def test_interaction_unknown_type_accepted(self):
        interaction = Interaction(
            source="a", target="b", summary="custom", interaction_type="custom_type"
        )
        assert interaction.interaction_type == "custom_type"


class TestInteractionSerialization:
    def test_to_dict_contains_all_fields(self, sample_interaction: Interaction):
        d = sample_interaction.to_dict()
        assert d["source"] == "main_agent"
        assert d["target"] == "researcher"
        assert d["interaction_type"] == "delegation"
        assert d["labels"] == {"priority": "high"}
        assert isinstance(d["timestamp"], str)
        assert isinstance(d["interaction_id"], str)

    def test_unknown_type_serializes(self):
        interaction = Interaction(
            source="a", target="b", summary="x", interaction_type="novel_kind"
        )
        d = interaction.to_dict()
        assert d["interaction_type"] == "novel_kind"


# ---------------------------------------------------------------------------
# EventStore: add and agent state
# ---------------------------------------------------------------------------


class TestEventStoreAdd:
    async def test_add_stores_event(self, event_store: EventStore, sample_event: Event):
        event_store.add(sample_event)
        summary = event_store.get_pipeline_summary()
        assert summary["event_count"] == 1

    async def test_add_creates_agent_state_on_start(
        self, event_store: EventStore, sample_event: Event
    ):
        event_store.add(sample_event)
        summary = event_store.get_pipeline_summary()
        agent = summary["agents"]["agent-001"]
        assert agent["status"] == "running"
        assert agent["agent_type"] == "researcher"

    async def test_add_stop_marks_complete(self, event_store: EventStore, sample_event: Event):
        event_store.add(sample_event)
        stop_event = Event(
            event_type=EventType.AGENT_STOP,
            agent_type="researcher",
            agent_id="agent-001",
        )
        event_store.add(stop_event)
        summary = event_store.get_pipeline_summary()
        assert summary["agents"]["agent-001"]["status"] == "complete"

    async def test_add_stop_sets_stopped_at(self, event_store: EventStore, sample_event: Event):
        event_store.add(sample_event)
        stop_event = Event(
            event_type=EventType.AGENT_STOP,
            agent_type="researcher",
            agent_id="agent-001",
        )
        event_store.add(stop_event)
        agent = event_store.get_pipeline_summary()["agents"]["agent-001"]
        assert agent["stopped_at"] is not None
        assert agent["stopped_at"] == stop_event.timestamp.isoformat()

    async def test_stopped_at_none_while_running(
        self, event_store: EventStore, sample_event: Event
    ):
        event_store.add(sample_event)
        agent = event_store.get_pipeline_summary()["agents"]["agent-001"]
        assert agent["stopped_at"] is None

    async def test_add_phase_transition_updates_state(
        self, event_store: EventStore, sample_event: Event, phase_event: Event
    ):
        event_store.add(sample_event)
        event_store.add(phase_event)
        agent = event_store.get_pipeline_summary()["agents"]["agent-001"]
        assert agent["current_phase"] == 2
        assert agent["total_phases"] == 5
        assert agent["phase_name"] == "analysis"

    async def test_add_error_marks_failed(self, event_store: EventStore, sample_event: Event):
        event_store.add(sample_event)
        error_event = Event(
            event_type=EventType.ERROR,
            agent_type="researcher",
            agent_id="agent-001",
            message="Something went wrong",
        )
        event_store.add(error_event)
        agent = event_store.get_pipeline_summary()["agents"]["agent-001"]
        assert agent["status"] == "failed"
        assert agent["last_message"] == "Something went wrong"

    async def test_phase_transition_updates_labels(
        self, event_store: EventStore, sample_event: Event
    ):
        event_store.add(sample_event)
        phase = Event(
            event_type=EventType.PHASE_TRANSITION,
            agent_type="researcher",
            agent_id="agent-001",
            phase=1,
            total_phases=5,
            phase_name="gather",
            labels={"scope": "narrow"},
        )
        event_store.add(phase)
        agent = event_store.get_pipeline_summary()["agents"]["agent-001"]
        assert agent["labels"]["scope"] == "narrow"
        # Original label from start event should also be present
        assert agent["labels"]["feature"] == "auth"


# ---------------------------------------------------------------------------
# EventStore: interactions and delegation
# ---------------------------------------------------------------------------


class TestEventStoreInteractions:
    async def test_add_interaction_stores(
        self, event_store: EventStore, sample_interaction: Interaction
    ):
        iid = event_store.add_interaction(sample_interaction)
        assert iid == sample_interaction.interaction_id
        summary = event_store.get_pipeline_summary()
        assert len(summary["interactions"]) == 1
        assert summary["interactions"][0]["interaction_type"] == "delegation"

    async def test_delegation_interaction_creates_hierarchy(self, event_store: EventStore):
        """Delegation interaction arrives after both agents already started."""
        parent_start = Event(
            event_type=EventType.AGENT_START, agent_type="main_agent", agent_id="main_agent"
        )
        child_start = Event(
            event_type=EventType.AGENT_START, agent_type="researcher", agent_id="researcher"
        )
        event_store.add(parent_start)
        event_store.add(child_start)

        delegation = Interaction(
            source="main_agent",
            target="researcher",
            summary="Delegate research",
            interaction_type="delegation",
        )
        event_store.add_interaction(delegation)

        summary = event_store.get_pipeline_summary()
        assert summary["agents"]["researcher"]["delegation_parent"] == "main_agent"
        assert "researcher" in summary["agents"]["main_agent"]["delegation_children"]

    async def test_delegation_sets_task_summary_on_existing_child(self, event_store: EventStore):
        """Delegation after both agents started captures task_summary on child."""
        parent_start = Event(
            event_type=EventType.AGENT_START, agent_type="main_agent", agent_id="main_agent"
        )
        child_start = Event(
            event_type=EventType.AGENT_START, agent_type="researcher", agent_id="researcher"
        )
        event_store.add(parent_start)
        event_store.add(child_start)

        delegation = Interaction(
            source="main_agent",
            target="researcher",
            summary="Investigate auth library options",
            interaction_type="delegation",
        )
        event_store.add_interaction(delegation)

        agent = event_store.get_pipeline_summary()["agents"]["researcher"]
        assert agent["task_summary"] == "Investigate auth library options"

    async def test_delegation_before_agent_start(self, event_store: EventStore):
        """Delegation interaction arrives before the target agent starts."""
        parent_start = Event(
            event_type=EventType.AGENT_START, agent_type="main_agent", agent_id="main_agent"
        )
        event_store.add(parent_start)

        delegation = Interaction(
            source="main_agent",
            target="researcher",
            summary="Delegate research",
            interaction_type="delegation",
        )
        event_store.add_interaction(delegation)

        # Now the target agent starts -- _apply_pending_delegation should link it
        child_start = Event(
            event_type=EventType.AGENT_START, agent_type="researcher", agent_id="researcher"
        )
        event_store.add(child_start)

        summary = event_store.get_pipeline_summary()
        assert summary["agents"]["researcher"]["delegation_parent"] == "main_agent"
        assert "researcher" in summary["agents"]["main_agent"]["delegation_children"]

    async def test_delegation_before_start_sets_task_summary(self, event_store: EventStore):
        """Task summary captured from pending delegation when agent starts later."""
        parent_start = Event(
            event_type=EventType.AGENT_START, agent_type="main_agent", agent_id="main_agent"
        )
        event_store.add(parent_start)

        delegation = Interaction(
            source="main_agent",
            target="researcher",
            summary="Audit database schema",
            interaction_type="delegation",
        )
        event_store.add_interaction(delegation)

        child_start = Event(
            event_type=EventType.AGENT_START, agent_type="researcher", agent_id="researcher"
        )
        event_store.add(child_start)

        agent = event_store.get_pipeline_summary()["agents"]["researcher"]
        assert agent["task_summary"] == "Audit database schema"

    async def test_delegation_without_agent_start(self, event_store: EventStore):
        """Delegation for an agent that never starts -- interaction in timeline, no corrupted state."""
        delegation = Interaction(
            source="main_agent",
            target="ghost_agent",
            summary="Delegate to nonexistent",
            interaction_type="delegation",
        )
        event_store.add_interaction(delegation)

        summary = event_store.get_pipeline_summary()
        assert len(summary["interactions"]) == 1
        assert summary["interactions"][0]["target"] == "ghost_agent"
        # No AgentState should exist for ghost_agent
        assert "ghost_agent" not in summary["agents"]
        # Delegation chain should still include it
        assert len(summary["delegation_chain"]) == 1
        assert summary["delegation_chain"][0]["child"] == "ghost_agent"

    async def test_non_delegation_interactions_do_not_affect_hierarchy(
        self, event_store: EventStore
    ):
        """Only delegation type creates hierarchy links."""
        parent_start = Event(
            event_type=EventType.AGENT_START, agent_type="main_agent", agent_id="main_agent"
        )
        child_start = Event(
            event_type=EventType.AGENT_START, agent_type="researcher", agent_id="researcher"
        )
        event_store.add(parent_start)
        event_store.add(child_start)

        for itype in ("query", "result", "decision", "response"):
            interaction = Interaction(
                source="main_agent",
                target="researcher",
                summary=f"Test {itype}",
                interaction_type=itype,
            )
            event_store.add_interaction(interaction)

        summary = event_store.get_pipeline_summary()
        assert summary["agents"]["researcher"]["delegation_parent"] == ""
        assert summary["agents"]["main_agent"]["delegation_children"] == []
        assert len(summary["interactions"]) == 4

    async def test_multiple_interaction_types_in_timeline(self, event_store: EventStore):
        """All 5 standard types plus unknown type appear in timeline."""
        interaction_types = ["query", "delegation", "result", "decision", "response", "custom"]
        for itype in interaction_types:
            interaction = Interaction(
                source="a", target="b", summary=f"Test {itype}", interaction_type=itype
            )
            event_store.add_interaction(interaction)

        summary = event_store.get_pipeline_summary()
        assert len(summary["interactions"]) == len(interaction_types)
        recorded_types = [i["interaction_type"] for i in summary["interactions"]]
        assert recorded_types == interaction_types


# ---------------------------------------------------------------------------
# EventStore: delegation chain
# ---------------------------------------------------------------------------


class TestDelegationChain:
    async def test_get_delegation_chain_from_delegation_interactions(self, event_store: EventStore):
        delegation = Interaction(
            source="main_agent",
            target="researcher",
            summary="Research auth options",
            interaction_type="delegation",
        )
        event_store.add_interaction(delegation)

        chain = event_store.get_delegation_chain()
        assert len(chain) == 1
        assert chain[0]["parent"] == "main_agent"
        assert chain[0]["child"] == "researcher"
        assert chain[0]["reason"] == "Research auth options"

    async def test_delegation_chain_excludes_non_delegation(self, event_store: EventStore):
        query = Interaction(
            source="user", target="main_agent", summary="Ask something", interaction_type="query"
        )
        delegation = Interaction(
            source="main_agent",
            target="researcher",
            summary="Delegate",
            interaction_type="delegation",
        )
        event_store.add_interaction(query)
        event_store.add_interaction(delegation)

        chain = event_store.get_delegation_chain()
        assert len(chain) == 1
        assert chain[0]["parent"] == "main_agent"


# ---------------------------------------------------------------------------
# EventStore: subscribe / unsubscribe
# ---------------------------------------------------------------------------


class TestSubscription:
    async def test_subscribe_receives_events(self, event_store: EventStore):
        queue = event_store.subscribe()
        event = Event(event_type=EventType.AGENT_START, agent_type="researcher")
        event_store.add(event)

        received = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert received.agent_type == "researcher"

    async def test_unsubscribe_stops_delivery(self, event_store: EventStore):
        queue = event_store.subscribe()
        event_store.unsubscribe(queue)

        event = Event(event_type=EventType.AGENT_START, agent_type="researcher")
        event_store.add(event)

        assert queue.empty()

    async def test_multiple_subscribers(self, event_store: EventStore):
        q1 = event_store.subscribe()
        q2 = event_store.subscribe()

        event = Event(event_type=EventType.AGENT_START, agent_type="researcher")
        event_store.add(event)

        r1 = await asyncio.wait_for(q1.get(), timeout=1.0)
        r2 = await asyncio.wait_for(q2.get(), timeout=1.0)
        assert r1.agent_type == "researcher"
        assert r2.agent_type == "researcher"

    async def test_interaction_broadcast_as_synthetic_event(self, event_store: EventStore):
        queue = event_store.subscribe()
        interaction = Interaction(
            source="main_agent",
            target="researcher",
            summary="Delegate",
            interaction_type="delegation",
        )
        event_store.add_interaction(interaction)

        received = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert received.event_type == EventType.TOOL_USE
        assert "interaction:delegation:researcher" in received.message


# ---------------------------------------------------------------------------
# EventStore: pipeline summary
# ---------------------------------------------------------------------------


class TestPipelineSummary:
    async def test_summary_structure(self, event_store: EventStore):
        summary = event_store.get_pipeline_summary()
        assert "agents" in summary
        assert "interactions" in summary
        assert "delegation_chain" in summary
        assert "event_count" in summary
        assert "recent_events" in summary

    async def test_summary_with_data(self, event_store: EventStore, sample_event: Event):
        event_store.add(sample_event)
        interaction = Interaction(
            source="main_agent",
            target="researcher",
            summary="Delegate",
            interaction_type="delegation",
        )
        event_store.add_interaction(interaction)

        summary = event_store.get_pipeline_summary()
        assert len(summary["agents"]) == 1
        assert len(summary["interactions"]) == 1
        assert len(summary["delegation_chain"]) == 1
        assert summary["event_count"] == 1
        assert len(summary["recent_events"]) == 1


# ---------------------------------------------------------------------------
# EventStore: get_events_by_agent with label filtering
# ---------------------------------------------------------------------------


class TestGetEventsByAgent:
    async def test_filters_by_agent_type(self, event_store: EventStore):
        e1 = Event(event_type=EventType.AGENT_START, agent_type="researcher")
        e2 = Event(event_type=EventType.AGENT_START, agent_type="architect")
        event_store.add(e1)
        event_store.add(e2)

        results = event_store.get_events_by_agent("researcher")
        assert len(results) == 1
        assert results[0]["agent_type"] == "researcher"

    async def test_respects_limit(self, event_store: EventStore):
        for i in range(10):
            e = Event(
                event_type=EventType.PHASE_TRANSITION,
                agent_type="researcher",
                phase=i,
            )
            event_store.add(e)

        results = event_store.get_events_by_agent("researcher", limit=3)
        assert len(results) == 3

    async def test_label_filter_key_value(self, event_store: EventStore):
        e1 = Event(
            event_type=EventType.AGENT_START,
            agent_type="researcher",
            labels={"feature": "auth"},
        )
        e2 = Event(
            event_type=EventType.AGENT_START,
            agent_type="researcher",
            labels={"feature": "db"},
        )
        event_store.add(e1)
        event_store.add(e2)

        results = event_store.get_events_by_agent("researcher", label="feature=auth")
        assert len(results) == 1
        assert results[0]["labels"]["feature"] == "auth"

    async def test_label_filter_key_exists(self, event_store: EventStore):
        e1 = Event(
            event_type=EventType.AGENT_START,
            agent_type="researcher",
            labels={"observability": ""},
        )
        e2 = Event(
            event_type=EventType.AGENT_START,
            agent_type="researcher",
            labels={},
        )
        event_store.add(e1)
        event_store.add(e2)

        results = event_store.get_events_by_agent("researcher", label="observability")
        assert len(results) == 1

    async def test_no_label_filter_returns_all(self, event_store: EventStore):
        e1 = Event(
            event_type=EventType.AGENT_START,
            agent_type="researcher",
            labels={"feature": "auth"},
        )
        e2 = Event(
            event_type=EventType.AGENT_START,
            agent_type="researcher",
            labels={},
        )
        event_store.add(e1)
        event_store.add(e2)

        results = event_store.get_events_by_agent("researcher", label=None)
        assert len(results) == 2


# ---------------------------------------------------------------------------
# EventStore: bounded deque
# ---------------------------------------------------------------------------


class TestBoundedDeque:
    async def test_events_beyond_maxlen_are_dropped(self):
        small_store = EventStore(max_events=5)
        for i in range(10):
            e = Event(
                event_type=EventType.PHASE_TRANSITION,
                agent_type="researcher",
                phase=i,
                message=f"phase-{i}",
            )
            small_store.add(e)

        summary = small_store.get_pipeline_summary()
        assert summary["event_count"] == 5
        # Oldest events (phase 0-4) should be dropped, newest (5-9) kept
        recent = summary["recent_events"]
        phases = [e["phase"] for e in recent]
        assert phases == [5, 6, 7, 8, 9]
