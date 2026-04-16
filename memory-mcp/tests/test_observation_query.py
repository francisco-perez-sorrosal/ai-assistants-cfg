"""Tests for `ObservationStore.query()` trace/span correlation filters.

Per ADR dec-048 §Query model, `query()` gains top-level `trace_id` and
`span_id` keyword filters (field-equality, full-scan over the append-only
JSONL — acceptable for current sizes). Empty result sets return an empty
list; non-matching inputs never raise.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from memory_mcp.observations import ObservationStore

# -- Reference values ---------------------------------------------------------

TRACE_ID_A = "0af7651916cd43dd8448eb211c80319c"
TRACE_ID_B = "11112222333344445555666677778888"
SPAN_ID_A = "00f067aa0ba902b7"
SPAN_ID_B = "aaaabbbbccccdddd"


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def obs_file(tmp_path: Path) -> Path:
    """Return a path for a new observations JSONL file (not yet created)."""
    return tmp_path / "observations.jsonl"


@pytest.fixture
def store(obs_file: Path) -> ObservationStore:
    """Return an ObservationStore backed by a fresh path."""
    return ObservationStore(obs_file)


def _row(
    *,
    timestamp: str = "2026-04-16T10:00:00Z",
    session_id: str = "sess-1",
    agent_type: str = "implementer",
    agent_id: str = "impl-1",
    project: str = "praxion",
    event_type: str = "tool_use",
    tool_name: str | None = "remember",
    trace_id: str | None = None,
    span_id: str | None = None,
    traceparent: str | None = None,
) -> dict:
    """Build an observation row with optional correlation fields."""
    row: dict = {
        "timestamp": timestamp,
        "session_id": session_id,
        "agent_type": agent_type,
        "agent_id": agent_id,
        "project": project,
        "event_type": event_type,
        "tool_name": tool_name,
        "file_paths": [],
        "outcome": "success",
        "classification": None,
        "metadata": {},
    }
    if trace_id is not None:
        row["trace_id"] = trace_id
    if span_id is not None:
        row["span_id"] = span_id
    if traceparent is not None:
        row["traceparent"] = traceparent
    return row


# -- Filter by trace_id -------------------------------------------------------


class TestQueryByTraceId:
    """`query(trace_id=...)` returns only rows matching that trace."""

    def test_returns_only_rows_matching_trace_id(self, store: ObservationStore):
        """Among three rows, only the one with the matching trace_id is returned."""
        store.append(_row(trace_id=TRACE_ID_A, span_id=SPAN_ID_A))
        store.append(_row(trace_id=TRACE_ID_B, span_id=SPAN_ID_B))
        store.append(_row())  # no correlation fields

        results = store.query(trace_id=TRACE_ID_A)
        assert len(results) == 1
        assert results[0]["trace_id"] == TRACE_ID_A

    def test_multiple_rows_under_same_trace_all_returned(self, store: ObservationStore):
        """Two rows sharing a trace_id (different spans) both match."""
        store.append(_row(trace_id=TRACE_ID_A, span_id=SPAN_ID_A))
        store.append(_row(trace_id=TRACE_ID_A, span_id=SPAN_ID_B))
        store.append(_row(trace_id=TRACE_ID_B, span_id=SPAN_ID_A))

        results = store.query(trace_id=TRACE_ID_A)
        assert len(results) == 2
        assert all(r["trace_id"] == TRACE_ID_A for r in results)

    def test_non_matching_trace_id_returns_empty(self, store: ObservationStore):
        """A trace_id absent from the store yields an empty result, not an error."""
        store.append(_row(trace_id=TRACE_ID_A, span_id=SPAN_ID_A))

        results = store.query(trace_id="ffffffffffffffffffffffffffffffff")
        assert results == []

    def test_trace_id_filter_on_empty_store_returns_empty(self, store: ObservationStore):
        """Filtering an empty store returns an empty list, not None."""
        results = store.query(trace_id=TRACE_ID_A)
        assert results == []

    def test_trace_id_filter_ignores_rows_without_field(self, store: ObservationStore):
        """Historical rows with no trace_id field are excluded from matches."""
        store.append(_row())  # no trace_id
        store.append(_row(trace_id=TRACE_ID_A, span_id=SPAN_ID_A))

        results = store.query(trace_id=TRACE_ID_A)
        assert len(results) == 1
        assert results[0]["trace_id"] == TRACE_ID_A


# -- Filter by span_id --------------------------------------------------------


class TestQueryBySpanId:
    """`query(span_id=...)` returns only rows matching that span."""

    def test_returns_only_rows_matching_span_id(self, store: ObservationStore):
        store.append(_row(trace_id=TRACE_ID_A, span_id=SPAN_ID_A))
        store.append(_row(trace_id=TRACE_ID_A, span_id=SPAN_ID_B))

        results = store.query(span_id=SPAN_ID_A)
        assert len(results) == 1
        assert results[0]["span_id"] == SPAN_ID_A

    def test_non_matching_span_id_returns_empty(self, store: ObservationStore):
        store.append(_row(trace_id=TRACE_ID_A, span_id=SPAN_ID_A))

        results = store.query(span_id="0000000000000000")
        assert results == []


# -- Combined trace_id + span_id ---------------------------------------------


class TestQueryByBoth:
    """Supplying both filters narrows the result to rows matching both."""

    def test_both_filters_applied_conjunctively(self, store: ObservationStore):
        """Row must match trace_id AND span_id — AND semantics, not OR."""
        store.append(_row(trace_id=TRACE_ID_A, span_id=SPAN_ID_A))
        store.append(_row(trace_id=TRACE_ID_A, span_id=SPAN_ID_B))
        store.append(_row(trace_id=TRACE_ID_B, span_id=SPAN_ID_A))

        results = store.query(trace_id=TRACE_ID_A, span_id=SPAN_ID_A)
        assert len(results) == 1
        assert results[0]["trace_id"] == TRACE_ID_A
        assert results[0]["span_id"] == SPAN_ID_A

    def test_both_filters_with_no_overlap_returns_empty(self, store: ObservationStore):
        """Valid filters that share no row return empty — no partial match."""
        store.append(_row(trace_id=TRACE_ID_A, span_id=SPAN_ID_A))
        store.append(_row(trace_id=TRACE_ID_B, span_id=SPAN_ID_B))

        results = store.query(trace_id=TRACE_ID_A, span_id=SPAN_ID_B)
        assert results == []


# -- Interaction with existing filters ---------------------------------------


class TestQueryCombinedWithExistingFilters:
    """Trace filters compose cleanly with pre-existing session_id filter."""

    def test_trace_id_with_session_id_both_apply(self, store: ObservationStore):
        """Combining session_id and trace_id narrows to their intersection."""
        store.append(_row(session_id="sess-1", trace_id=TRACE_ID_A, span_id=SPAN_ID_A))
        store.append(_row(session_id="sess-2", trace_id=TRACE_ID_A, span_id=SPAN_ID_B))
        store.append(_row(session_id="sess-1"))  # no correlation

        results = store.query(session_id="sess-1", trace_id=TRACE_ID_A)
        assert len(results) == 1
        assert results[0]["session_id"] == "sess-1"
        assert results[0]["trace_id"] == TRACE_ID_A

    def test_no_filters_returns_all_rows(self, store: ObservationStore):
        """Baseline: without filters, all appended rows are returned."""
        store.append(_row(trace_id=TRACE_ID_A, span_id=SPAN_ID_A))
        store.append(_row(trace_id=TRACE_ID_B, span_id=SPAN_ID_B))
        store.append(_row())

        results = store.query()
        assert len(results) == 3
