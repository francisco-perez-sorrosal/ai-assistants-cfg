"""W3C trace-context correlation helpers.

Parses the W3C traceparent header (https://www.w3.org/TR/trace-context/) into
its ``trace_id`` and ``span_id`` components. The parser is strict on format:
version ``00`` only, hex-only identifiers, all-zero ids rejected.

Used by memory-mcp tool handlers to extract trace/span IDs from the MCP
``params._meta.traceparent`` envelope and forward them to the observation
layer via hook ``additionalContext``.
"""

from __future__ import annotations

import re

# -- Constants ----------------------------------------------------------------

# W3C traceparent: version(2) "-" trace-id(32) "-" span-id(16) "-" flags(2)
# Total: 55 characters. Only version "00" is defined today; we reject others
# to avoid silently ingesting an undefined future format.
_TRACEPARENT_RE = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-[0-9a-f]{2}$")

_INVALID_TRACE_ID = "0" * 32
_INVALID_SPAN_ID = "0" * 16


def parse_traceparent(value: str) -> tuple[str, str] | None:
    """Parse a W3C traceparent header into ``(trace_id, span_id)``.

    Returns ``None`` when the input is malformed, uses an unsupported version,
    or carries the all-zero invalid-id sentinels reserved by the spec.

    Args:
        value: The raw ``traceparent`` header value
            (e.g. ``"00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"``).

    Returns:
        ``(trace_id, span_id)`` tuple of lowercase-hex strings on success;
        ``None`` on any validation failure.
    """
    if not isinstance(value, str):
        return None

    match = _TRACEPARENT_RE.match(value)
    if match is None:
        return None

    trace_id, span_id = match.group(1), match.group(2)

    # Reject the all-zero sentinels — spec treats these as "invalid".
    if trace_id == _INVALID_TRACE_ID or span_id == _INVALID_SPAN_ID:
        return None

    return trace_id, span_id
