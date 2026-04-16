"""End-to-end correlation round-trip: MCP tool handler → hook → observation row.

Covers ADR dec-048 §Phase B acceptance criteria from SYSTEMS_PLAN.md §4.6:

1. ``remember()``/``recall()`` parse ``params._meta.traceparent`` when present
   and surface extracted ``trace_id``/``span_id`` via ``additionalContext`` on
   the tool response.
2. ``capture_memory.py`` reads ``additionalContext.trace_id``/``span_id`` from
   the PostToolUse payload and populates the Observation row.
3. ``ObservationStore.query(trace_id=...)`` finds the written row exactly.
4. When traceparent is absent/malformed, the row lands with empty strings and
   no crash.

The hook is imported by file path (it lives outside the ``memory_mcp`` package
and is not installable). The MCP side is exercised by driving the tool
handler (``remember`` / ``recall``) directly — the FastMCP-decorated functions
remain plain callables, so injecting a stub ``Context`` is a natural unit.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path
from typing import Any

import pytest

from memory_mcp import server as mcp_server
from memory_mcp.observations import ObservationStore

# -- Reference vectors --------------------------------------------------------

TRACE_ID = "0af7651916cd43dd8448eb211c80319c"
SPAN_ID = "00f067aa0ba902b7"
TRACEPARENT = f"00-{TRACE_ID}-{SPAN_ID}-01"

HOOK_PATH = Path(__file__).resolve().parents[2] / "hooks" / "capture_memory.py"


# -- Module loading helpers ---------------------------------------------------


def _load_capture_memory_module() -> types.ModuleType:
    """Import ``hooks/capture_memory.py`` as a module by file path.

    ``capture_memory.py`` imports ``_hook_utils`` from its own directory; we
    prepend that directory to ``sys.path`` so the import resolves at load
    time.
    """
    hooks_dir = str(HOOK_PATH.parent)
    if hooks_dir not in sys.path:
        sys.path.insert(0, hooks_dir)
    spec = importlib.util.spec_from_file_location("capture_memory", HOOK_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# -- Stubs --------------------------------------------------------------------


class _StubMeta:
    """Mimic ``RequestParams.Meta`` — pydantic model with extra='allow'.

    The real MCP SDK models ``_meta`` as a pydantic BaseModel whose
    ``extra="allow"`` config surfaces arbitrary fields (like ``traceparent``)
    as regular attributes. A duck-typed object with the matching attribute is
    all our ``_extract_correlation`` needs.
    """

    def __init__(self, *, traceparent: str | None = None) -> None:
        self.traceparent = traceparent


class _StubRequestContext:
    """Mimic ``RequestContext`` — only the ``meta`` attribute is consumed."""

    def __init__(self, meta: _StubMeta | None) -> None:
        self.meta = meta


class _StubContext:
    """Mimic ``mcp.server.fastmcp.Context`` — only ``request_context`` is read."""

    def __init__(self, traceparent: str | None) -> None:
        meta = _StubMeta(traceparent=traceparent) if traceparent is not None else None
        self._ctx = _StubRequestContext(meta)

    @property
    def request_context(self) -> _StubRequestContext:
        return self._ctx


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def ai_state_dir(tmp_path: Path) -> Path:
    """Create an ``.ai-state/`` directory under tmp_path (hook guards on its existence)."""
    ai_state = tmp_path / ".ai-state"
    ai_state.mkdir()
    return ai_state


@pytest.fixture
def obs_path(ai_state_dir: Path) -> Path:
    """Return the canonical observations.jsonl path under ai_state_dir."""
    return ai_state_dir / "observations.jsonl"


@pytest.fixture
def memory_file(ai_state_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate MemoryStore to a fresh tmp memory.json; reset the singleton."""
    mem = ai_state_dir / "memory.json"
    monkeypatch.setenv("MEMORY_FILE", str(mem))
    monkeypatch.setattr(mcp_server, "_store", None)
    return mem


@pytest.fixture
def capture_memory_module() -> types.ModuleType:
    """Return the imported capture_memory hook module."""
    return _load_capture_memory_module()


# -- Helpers ------------------------------------------------------------------


def _run_hook(
    module: types.ModuleType,
    payload: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Feed a synthetic PostToolUse payload into the hook and run ``main()``."""
    monkeypatch.setattr(module.sys, "stdin", _StringIO(json.dumps(payload)))
    # DISABLE_OBSERVABILITY must not be set; clear just in case.
    monkeypatch.delenv(module.DISABLE_OBSERVABILITY, raising=False)
    module.main()


class _StringIO:
    """Minimal stdin stand-in — only ``.read()`` is invoked by the hook."""

    def __init__(self, data: str) -> None:
        self._data = data

    def read(self) -> str:
        return self._data


# -- Case 1: traceparent present, full round-trip -----------------------------


class TestCorrelationRoundTripWithTraceparent:
    """End-to-end: remember() with traceparent → hook writes → query returns row."""

    def test_remember_response_carries_additional_context(self, memory_file: Path) -> None:
        """The tool handler attaches ``additionalContext`` with parsed IDs."""
        ctx = _StubContext(traceparent=TRACEPARENT)
        response = mcp_server.remember(
            category="learnings",
            key="correlation-roundtrip-test",
            value="round-trip test marker",
            force=True,
            ctx=ctx,  # type: ignore[arg-type]
        )
        assert response.get("additionalContext") == {
            "trace_id": TRACE_ID,
            "span_id": SPAN_ID,
            "traceparent": TRACEPARENT,
            "parent_span_id": "",
        }

    def test_hook_writes_observation_with_correlation(
        self,
        memory_file: Path,
        obs_path: Path,
        ai_state_dir: Path,
        capture_memory_module: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Hook consumes handler's response and writes trace_id into the row."""
        ctx = _StubContext(traceparent=TRACEPARENT)
        tool_response = mcp_server.remember(
            category="learnings",
            key="correlation-roundtrip-write",
            value="round-trip test marker",
            force=True,
            ctx=ctx,  # type: ignore[arg-type]
        )
        payload = {
            "tool_name": "remember",
            "tool_input": {"category": "learnings", "key": "correlation-roundtrip-write"},
            "tool_response": tool_response,
            "cwd": str(ai_state_dir.parent),
            "session_id": "sess-roundtrip",
            "agent_type": "implementer",
        }
        _run_hook(capture_memory_module, payload, monkeypatch)

        assert obs_path.exists(), "hook must create observations.jsonl"
        lines = obs_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        row = json.loads(lines[0])
        assert row["trace_id"] == TRACE_ID
        assert row["span_id"] == SPAN_ID

    def test_query_returns_exactly_the_written_row(
        self,
        memory_file: Path,
        obs_path: Path,
        ai_state_dir: Path,
        capture_memory_module: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """ObservationStore.query(trace_id=...) recovers the written observation."""
        ctx = _StubContext(traceparent=TRACEPARENT)
        tool_response = mcp_server.remember(
            category="learnings",
            key="correlation-roundtrip-query",
            value="round-trip test marker",
            force=True,
            ctx=ctx,  # type: ignore[arg-type]
        )
        payload = {
            "tool_name": "remember",
            "tool_input": {"category": "learnings", "key": "correlation-roundtrip-query"},
            "tool_response": tool_response,
            "cwd": str(ai_state_dir.parent),
            "session_id": "sess-roundtrip",
            "agent_type": "implementer",
        }
        _run_hook(capture_memory_module, payload, monkeypatch)

        store = ObservationStore(obs_path)
        results = store.query(trace_id=TRACE_ID)
        assert len(results) == 1
        assert results[0]["tool_name"] == "remember"
        assert results[0]["trace_id"] == TRACE_ID
        assert results[0]["span_id"] == SPAN_ID


# -- Case 2: traceparent absent, graceful degradation -------------------------


class TestRoundTripWithoutTraceparent:
    """When no traceparent is present, correlation fields are empty strings."""

    def test_remember_response_has_empty_correlation(self, memory_file: Path) -> None:
        """Handler with no traceparent still emits additionalContext, all empty."""
        ctx = _StubContext(traceparent=None)
        response = mcp_server.remember(
            category="learnings",
            key="no-traceparent-key",
            value="marker",
            force=True,
            ctx=ctx,  # type: ignore[arg-type]
        )
        assert response.get("additionalContext") == {
            "trace_id": "",
            "span_id": "",
            "traceparent": "",
            "parent_span_id": "",
        }

    def test_hook_writes_empty_strings_and_no_crash(
        self,
        memory_file: Path,
        obs_path: Path,
        ai_state_dir: Path,
        capture_memory_module: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Observation row lands with empty trace_id/span_id; hook does not raise."""
        ctx = _StubContext(traceparent=None)
        tool_response = mcp_server.remember(
            category="learnings",
            key="no-tp-row",
            value="marker",
            force=True,
            ctx=ctx,  # type: ignore[arg-type]
        )
        payload = {
            "tool_name": "remember",
            "tool_input": {"category": "learnings", "key": "no-tp-row"},
            "tool_response": tool_response,
            "cwd": str(ai_state_dir.parent),
            "session_id": "sess-empty",
            "agent_type": "implementer",
        }
        _run_hook(capture_memory_module, payload, monkeypatch)

        lines = obs_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        row = json.loads(lines[0])
        assert row["trace_id"] == ""
        assert row["span_id"] == ""

    def test_recall_handler_also_produces_additional_context(self, memory_file: Path) -> None:
        """``recall()`` surfaces the same additionalContext shape as ``remember()``.

        ``recall()`` on an empty category raises KeyError internally; the
        error branch still emits ``additionalContext`` per handler contract.
        """
        ctx = _StubContext(traceparent=TRACEPARENT)
        # Seed one entry so recall succeeds.
        mcp_server.remember(
            category="learnings",
            key="recall-target",
            value="marker",
            force=True,
        )
        response = mcp_server.recall(
            category="learnings",
            key="recall-target",
            ctx=ctx,  # type: ignore[arg-type]
        )
        assert response.get("additionalContext") == {
            "trace_id": TRACE_ID,
            "span_id": SPAN_ID,
            "traceparent": TRACEPARENT,
            "parent_span_id": "",
        }


# -- Case 3: malformed traceparent — handled as absent ------------------------


class TestMalformedTraceparent:
    """Invalid traceparent yields empty correlation, not an exception."""

    @pytest.mark.parametrize(
        "bad_value",
        [
            "not-a-traceparent",
            "00-xyz-abc-01",  # non-hex
            "00-" + "0" * 32 + "-" + "0" * 16 + "-01",  # all-zero sentinel
            "",
        ],
    )
    def test_malformed_traceparent_degrades_to_empty(
        self, memory_file: Path, bad_value: str
    ) -> None:
        """Any parse failure produces empty-string correlation fields."""
        ctx = _StubContext(traceparent=bad_value)
        response = mcp_server.remember(
            category="learnings",
            key=f"bad-tp-{hash(bad_value)}",
            value="marker",
            force=True,
            ctx=ctx,  # type: ignore[arg-type]
        )
        ac = response.get("additionalContext")
        assert ac == {"trace_id": "", "span_id": "", "traceparent": "", "parent_span_id": ""}


# -- Case 4: ctx=None path is safe --------------------------------------------


def test_extract_correlation_with_none_context_returns_empty() -> None:
    """Passing ``None`` to ``_extract_correlation`` yields empty fields."""
    result = mcp_server._extract_correlation(None)
    assert result == {"trace_id": "", "span_id": "", "traceparent": "", "parent_span_id": ""}
