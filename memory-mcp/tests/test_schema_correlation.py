"""Tests for correlation fields on the Observation dataclass.

Per ADR dec-048 §Phase A, `Observation` gains three top-level correlation
fields — `trace_id`, `span_id`, `traceparent` — populated by the hook from
`additionalContext` emitted by memory-mcp tool handlers that extracted the
W3C trace-context header. Fields are optional; historical rows without them
must still deserialize cleanly.
"""

from __future__ import annotations

from dataclasses import fields

from memory_mcp.schema import Observation

# -- Reference values ---------------------------------------------------------

TRACE_ID = "0af7651916cd43dd8448eb211c80319c"
SPAN_ID = "00f067aa0ba902b7"
TRACEPARENT = f"00-{TRACE_ID}-{SPAN_ID}-01"


def _minimal_kwargs() -> dict:
    """Return the base required fields common to every observation."""
    return {
        "timestamp": "2026-04-16T10:00:00Z",
        "session_id": "sess-abc",
        "agent_type": "implementer",
        "agent_id": "impl-1",
        "project": "praxion",
        "event_type": "tool_use",
    }


# -- Field presence -----------------------------------------------------------


class TestCorrelationFieldPresence:
    """Observation declares the three correlation fields at dataclass level."""

    def test_trace_id_is_declared_field(self):
        """`trace_id` is a top-level dataclass field, not metadata."""
        field_names = {f.name for f in fields(Observation)}
        assert "trace_id" in field_names

    def test_span_id_is_declared_field(self):
        """`span_id` is a top-level dataclass field, not metadata."""
        field_names = {f.name for f in fields(Observation)}
        assert "span_id" in field_names

    def test_traceparent_is_declared_field(self):
        """`traceparent` is a top-level dataclass field, not metadata."""
        field_names = {f.name for f in fields(Observation)}
        assert "traceparent" in field_names


# -- Defaults -----------------------------------------------------------------


class TestCorrelationFieldDefaults:
    """Correlation fields default to an absent value when not supplied."""

    def test_trace_id_defaults_when_omitted(self):
        """Creating an Observation without trace_id does not require it."""
        obs = Observation(**_minimal_kwargs())
        # Contract: Optional[str] — either None or empty string counts as absent.
        assert obs.trace_id in (None, "")

    def test_span_id_defaults_when_omitted(self):
        obs = Observation(**_minimal_kwargs())
        assert obs.span_id in (None, "")

    def test_traceparent_defaults_when_omitted(self):
        obs = Observation(**_minimal_kwargs())
        assert obs.traceparent in (None, "")

    def test_to_dict_includes_correlation_fields_at_top_level(self):
        """Serialized form surfaces correlation fields as top-level keys.

        Per ADR dec-048: top-level, not nested under `metadata`, to match
        Datadog/OTel log-correlation conventions and keep JSONL grep-friendly.
        """
        obs = Observation(**_minimal_kwargs())
        data = obs.to_dict()
        assert "trace_id" in data
        assert "span_id" in data
        assert "traceparent" in data
        assert "trace_id" not in data.get("metadata", {})
        assert "span_id" not in data.get("metadata", {})


# -- Round-trip with correlation populated ------------------------------------


class TestRoundTripWithCorrelation:
    """Round-trip preserves populated correlation fields verbatim."""

    def test_populated_round_trip_preserves_trace_id(self):
        obs = Observation(
            **_minimal_kwargs(),
            trace_id=TRACE_ID,
            span_id=SPAN_ID,
            traceparent=TRACEPARENT,
        )
        restored = Observation.from_dict(obs.to_dict())
        assert restored.trace_id == TRACE_ID
        assert restored.span_id == SPAN_ID
        assert restored.traceparent == TRACEPARENT

    def test_round_trip_emits_expected_keys(self):
        """to_dict output contains exactly the populated correlation values."""
        obs = Observation(
            **_minimal_kwargs(),
            trace_id=TRACE_ID,
            span_id=SPAN_ID,
            traceparent=TRACEPARENT,
        )
        data = obs.to_dict()
        assert data["trace_id"] == TRACE_ID
        assert data["span_id"] == SPAN_ID
        assert data["traceparent"] == TRACEPARENT

    def test_populated_round_trip_preserves_equality(self):
        """A round-tripped populated observation equals the original."""
        obs = Observation(
            **_minimal_kwargs(),
            trace_id=TRACE_ID,
            span_id=SPAN_ID,
            traceparent=TRACEPARENT,
        )
        restored = Observation.from_dict(obs.to_dict())
        assert restored == obs


# -- Round-trip without correlation (backward compatibility) ------------------


class TestRoundTripWithoutCorrelation:
    """Historical rows lacking correlation fields must parse cleanly."""

    def test_from_dict_without_correlation_fields(self):
        """A legacy observation dict (no correlation keys) deserializes.

        ADR dec-048 §Migration: no backfill; historical rows read as absent
        via `dict.get("trace_id", <default>)`. This must not raise.
        """
        data = {
            "timestamp": "2026-04-16T10:00:00Z",
            "session_id": "sess-abc",
            "agent_type": "implementer",
            "agent_id": "impl-1",
            "project": "praxion",
            "event_type": "tool_use",
        }
        obs = Observation.from_dict(data)
        assert obs.trace_id in (None, "")
        assert obs.span_id in (None, "")
        assert obs.traceparent in (None, "")

    def test_unpopulated_round_trip_has_stable_shape(self):
        """to_dict → from_dict → to_dict is idempotent when correlation absent."""
        obs = Observation(**_minimal_kwargs())
        first = obs.to_dict()
        restored = Observation.from_dict(first)
        second = restored.to_dict()
        assert first == second

    def test_partial_correlation_round_trip(self):
        """Observations with only trace_id (no span_id) still round-trip.

        This mirrors the Phase C case where only the trace is known.
        """
        obs = Observation(
            **_minimal_kwargs(),
            trace_id=TRACE_ID,
        )
        restored = Observation.from_dict(obs.to_dict())
        assert restored.trace_id == TRACE_ID
        assert restored.span_id in (None, "")
        assert restored.traceparent in (None, "")
