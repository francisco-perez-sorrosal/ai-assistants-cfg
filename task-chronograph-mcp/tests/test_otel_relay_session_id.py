"""Behavioral tests for the ``praxion.session_id`` → ``session.id`` rename (dec-048).

These tests encode the post-rename contract:

- **session.id** (OpenInference canonical) is present on every session, agent, and tool span.
- **praxion.session_id** (the deprecated, vendor-prefixed name) is absent from every span.
- Tool spans inherit ``session.id`` from their parent agent context — this is the new
  behaviour introduced by Phase A of dec-048; tool spans previously carried no session
  attribute at all.
- When a tool/agent is created without a parent session context, the attribute is *absent*
  rather than an empty string — "not set" and "explicitly empty" must remain
  distinguishable for downstream Phoenix filtering.
- The attribute survives serialisation to the in-memory OTel export format verbatim
  (OpenInference exporters do not transform the key).

These tests are written concurrently with the Step 3 implementer. They are expected to
fail until ``otel_relay.py`` applies the rename. They do not modify production code.
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import patch

import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

# ---------------------------------------------------------------------------
# Constants and helpers
# ---------------------------------------------------------------------------

# Canonical OpenInference attribute key. Intentionally hardcoded (not imported
# from openinference.semconv) so that a test failure immediately surfaces the
# literal string the contract pins to, independent of library upgrades.
SESSION_ID_KEY = "session.id"

# Deprecated vendor-prefixed key that dec-048 removes from every span.
LEGACY_SESSION_ID_KEY = "praxion.session_id"

PROJECT_DIR = "/tmp/test-session-id-project"
SESSION_ID = "sess-corr-042"
SESSION_SPAN_NAME = "session"
MAIN_AGENT_ID = "__main_agent__"


class OTelRelayTestHarness:
    """Wraps an OTelRelay with an InMemorySpanExporter for attribute inspection.

    Mirrors the pattern used by ``test_otel_relay.py`` so reviewers can compare
    the two files side-by-side. Only the behavioral slice relevant to the
    session-id rename is exercised here.
    """

    def __init__(self, *, otel_enabled: bool = True) -> None:
        self.exporter = InMemorySpanExporter()

        self._env_patcher = patch.dict(os.environ, {"OTEL_ENABLED": str(otel_enabled).lower()})
        self._env_patcher.start()

        # Late import: environment must be set before the module is imported so
        # any module-level env reads observe the test value.
        from task_chronograph_mcp.otel_relay import OTelRelay

        self.relay = OTelRelay(exporter=self.exporter)

    def teardown(self) -> None:
        self.relay.shutdown()
        self._env_patcher.stop()

    @property
    def finished_spans(self):
        return self.exporter.get_finished_spans()

    def session_span(self):
        matches = [s for s in self.finished_spans if s.name == SESSION_SPAN_NAME]
        assert len(matches) == 1, f"Expected 1 session span, found {len(matches)}"
        return matches[0]

    def spans_with_attribute(self, key: str, value: Any):
        return [s for s in self.finished_spans if s.attributes and s.attributes.get(key) == value]

    def agent_span(self, agent_id: str):
        matches = self.spans_with_attribute("praxion.agent_id", agent_id)
        assert len(matches) == 1, f"Expected 1 agent span for {agent_id}, found {len(matches)}"
        return matches[0]

    def tool_span(self, tool_name: str):
        matches = [
            s
            for s in self.finished_spans
            if s.attributes and s.attributes.get("tool.name") == tool_name
        ]
        assert len(matches) == 1, f"Expected 1 tool span for {tool_name}, found {len(matches)}"
        return matches[0]


@pytest.fixture
def harness():
    h = OTelRelayTestHarness()
    yield h
    h.teardown()


# ---------------------------------------------------------------------------
# 1. Session spans expose session.id (not praxion.session_id)
# ---------------------------------------------------------------------------


class TestSessionSpanCarriesCanonicalSessionId:
    """Session root spans must advertise the OpenInference canonical key."""

    def test_session_span_has_session_id_attribute(self, harness: OTelRelayTestHarness):
        harness.relay.start_session(SESSION_ID, PROJECT_DIR)
        harness.relay.end_session(SESSION_ID)

        root = harness.session_span()
        assert root.attributes[SESSION_ID_KEY] == SESSION_ID

    def test_session_span_does_not_use_legacy_praxion_session_id(
        self, harness: OTelRelayTestHarness
    ):
        harness.relay.start_session(SESSION_ID, PROJECT_DIR)
        harness.relay.end_session(SESSION_ID)

        root = harness.session_span()
        assert LEGACY_SESSION_ID_KEY not in root.attributes, (
            f"Session root span still emits deprecated {LEGACY_SESSION_ID_KEY!r}; "
            f"dec-048 Phase A requires the vendor-prefixed key be removed."
        )


# ---------------------------------------------------------------------------
# 2. Agent spans (main-agent + subagent) expose session.id
# ---------------------------------------------------------------------------


class TestAgentSpansCarrySessionId:
    """Both the synthetic main-agent span and subagent spans must carry session.id."""

    def test_main_agent_span_has_session_id(self, harness: OTelRelayTestHarness):
        harness.relay.start_session(SESSION_ID, PROJECT_DIR)
        harness.relay.end_session(SESSION_ID)

        main = harness.agent_span(MAIN_AGENT_ID)
        assert main.attributes[SESSION_ID_KEY] == SESSION_ID

    def test_subagent_span_has_session_id(self, harness: OTelRelayTestHarness):
        harness.relay.start_session(SESSION_ID, PROJECT_DIR)
        harness.relay.start_agent("agent-r1", "researcher", SESSION_ID)
        harness.relay.end_agent("agent-r1", "Done")
        harness.relay.end_session(SESSION_ID)

        agent = harness.agent_span("agent-r1")
        assert agent.attributes[SESSION_ID_KEY] == SESSION_ID


# ---------------------------------------------------------------------------
# 3. Tool spans inherit session.id from parent agent context
# ---------------------------------------------------------------------------


class TestToolSpansCarryInheritedSessionId:
    """Tool spans must expose session.id inherited from their parent agent.

    This is the NEW behaviour introduced by dec-048 Phase A. Before the fix,
    tool spans carried no session attribute at all, preventing trace↔memory
    joins via ``session.id`` for tool invocations.
    """

    def test_tool_span_under_main_agent_has_session_id(self, harness: OTelRelayTestHarness):
        harness.relay.start_session(SESSION_ID, PROJECT_DIR)
        harness.relay.record_tool(
            agent_id="",
            tool_name="Read",
            input_summary="/src/main.py",
            output_summary="...",
        )
        harness.relay.end_session(SESSION_ID)

        tool = harness.tool_span("Read")
        assert SESSION_ID_KEY in tool.attributes, (
            "Tool spans must carry session.id after dec-048 Phase A; "
            "inheritance from main-agent parent is missing."
        )
        assert tool.attributes[SESSION_ID_KEY] == SESSION_ID

    def test_tool_span_under_subagent_has_session_id(self, harness: OTelRelayTestHarness):
        harness.relay.start_session(SESSION_ID, PROJECT_DIR)
        harness.relay.start_agent("agent-i1", "implementer", SESSION_ID)
        harness.relay.record_tool(
            agent_id="agent-i1",
            tool_name="Write",
            input_summary="/dst/out.py",
            output_summary="ok",
        )
        harness.relay.end_agent("agent-i1", "Done")
        harness.relay.end_session(SESSION_ID)

        tool = harness.tool_span("Write")
        assert SESSION_ID_KEY in tool.attributes
        assert tool.attributes[SESSION_ID_KEY] == SESSION_ID

    def test_tool_span_session_id_matches_parent_agent_session_id(
        self, harness: OTelRelayTestHarness
    ):
        """The tool's session.id must equal its parent agent's session.id verbatim
        — inheritance, not independent re-computation."""
        harness.relay.start_session(SESSION_ID, PROJECT_DIR)
        harness.relay.start_agent("agent-i1", "implementer", SESSION_ID)
        harness.relay.record_tool(
            agent_id="agent-i1",
            tool_name="Bash",
            input_summary="ls",
            output_summary="file list",
        )
        harness.relay.end_agent("agent-i1", "Done")
        harness.relay.end_session(SESSION_ID)

        agent = harness.agent_span("agent-i1")
        tool = harness.tool_span("Bash")
        assert tool.attributes[SESSION_ID_KEY] == agent.attributes[SESSION_ID_KEY]


# ---------------------------------------------------------------------------
# 4. Negative: no span emits praxion.session_id anywhere
# ---------------------------------------------------------------------------


class TestNoSpanEmitsLegacyAttribute:
    """The rename must be complete — zero spans in the relay's output carry
    the deprecated vendor-prefixed key, regardless of span kind."""

    def test_full_session_produces_no_praxion_session_id(self, harness: OTelRelayTestHarness):
        # Exercise every span-producing path in one session so any lingering
        # emission site is caught by a single assertion.
        harness.relay.start_session(SESSION_ID, PROJECT_DIR)
        harness.relay.start_agent("agent-r1", "researcher", SESSION_ID)
        harness.relay.record_tool(
            agent_id="agent-r1",
            tool_name="Read",
            input_summary="f.py",
            output_summary="...",
        )
        harness.relay.add_phase_event(
            agent_id="agent-r1",
            phase=1,
            total=3,
            name="init",
            summary="Starting",
        )
        harness.relay.add_decision_event(
            agent_id="agent-r1",
            decision={
                "id": "dec-001",
                "category": "implementation",
                "text": "Use X",
                "made_by": "agent",
            },
        )
        harness.relay.record_skill("agent-r1", "testing-strategy", session_id=SESSION_ID)
        harness.relay.end_agent("agent-r1", "Findings...")
        harness.relay.end_session(SESSION_ID)

        offenders = [
            s
            for s in harness.finished_spans
            if s.attributes and LEGACY_SESSION_ID_KEY in s.attributes
        ]
        assert offenders == [], (
            f"Found {len(offenders)} spans still carrying {LEGACY_SESSION_ID_KEY!r}: "
            f"{[s.name for s in offenders]}"
        )


# ---------------------------------------------------------------------------
# 5. Absence semantics: no session context → attribute is absent, not ""
# ---------------------------------------------------------------------------


class TestSessionIdAbsentWhenNoParentContext:
    """When a span is created with no session context, ``session.id`` must be
    *absent* from the attribute map — not set to an empty string.

    Phoenix filtering treats "missing" and "empty string" as different buckets.
    Dec-048 explicitly chose absence for "no parent context" to avoid polluting
    the Sessions UI with blank-id entries.

    To exercise this code path without modifying production code, we call
    ``record_skill`` before any session is started. In the current relay,
    ``_record_skill_span`` short-circuits if ``_session_context`` is None — but
    lazy agent creation via tool events without an active session is the
    reliable way to produce a span with no session context attached.
    """

    def test_tool_span_before_session_start_has_no_session_id(self, harness: OTelRelayTestHarness):
        # No start_session — the relay should either suppress the span entirely
        # or, if it emits one, omit the session.id attribute.
        harness.relay.record_tool(
            agent_id="",
            tool_name="Read",
            input_summary="f.py",
            output_summary="...",
        )

        for span in harness.finished_spans:
            if span.attributes is None:
                continue
            if span.attributes.get("tool.name") == "Read":
                # If the relay emitted this orphan tool span at all, the
                # session.id key must be ABSENT (not "").
                assert SESSION_ID_KEY not in span.attributes, (
                    f"Orphan tool span emitted with {SESSION_ID_KEY}="
                    f"{span.attributes[SESSION_ID_KEY]!r}; absence is required "
                    f"when no session context exists (dec-048)."
                )


# ---------------------------------------------------------------------------
# 6. Serialization: session.id key survives in-memory export verbatim
# ---------------------------------------------------------------------------


class TestSessionIdSurvivesExportSerialization:
    """The InMemorySpanExporter is a faithful stand-in for the OTLP exporter:
    attribute keys pass through verbatim. Guard the canonical literal so a
    future exporter layer that rewrites keys (e.g., stripping dots for a
    different backend) would immediately fail this test.
    """

    def test_exported_span_contains_literal_session_id_key(self, harness: OTelRelayTestHarness):
        harness.relay.start_session(SESSION_ID, PROJECT_DIR)
        harness.relay.start_agent("agent-r1", "researcher", SESSION_ID)
        harness.relay.record_tool(
            agent_id="agent-r1",
            tool_name="Grep",
            input_summary="pattern",
            output_summary="matches",
        )
        harness.relay.end_agent("agent-r1", "Done")
        harness.relay.end_session(SESSION_ID)

        # Every span that logically has a session context must serialise the
        # canonical literal "session.id" — not "sessionId", not "session_id",
        # not "praxion.session.id".
        spans_with_session = [
            s
            for s in harness.finished_spans
            if s.name in {SESSION_SPAN_NAME, "researcher", "main-agent", "Grep"}
        ]
        assert spans_with_session, "Expected at least one span in the exported set"

        for span in spans_with_session:
            keys = list(span.attributes.keys()) if span.attributes else []
            # The canonical key must appear exactly once, with the canonical
            # spelling — no variants, no duplicates.
            matching = [k for k in keys if k == SESSION_ID_KEY]
            assert len(matching) == 1, (
                f"Span {span.name!r} should expose exactly one {SESSION_ID_KEY!r} key "
                f"after export; got {matching} (all keys: {keys})"
            )
            # And no near-miss variant slipped through.
            near_misses = [
                k
                for k in keys
                if k != SESSION_ID_KEY
                and "session" in k.lower()
                and "id" in k.lower()
                # Exclude openinference/otel semantic keys that legitimately
                # contain "session" and "id" but are not the session attribute
                # (e.g., parent_session_id and mcp.session.id are additive and
                # intentional).
                and k not in {"praxion.parent_session_id", "mcp.session.id"}
            ]
            assert near_misses == [], (
                f"Span {span.name!r} exports unexpected session-id variant keys: "
                f"{near_misses}. Only {SESSION_ID_KEY!r} is canonical."
            )
