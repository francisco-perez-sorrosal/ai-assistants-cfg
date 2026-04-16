"""Tests for the W3C traceparent parser in memory_mcp.correlation.

The `parse_traceparent` helper extracts `(trace_id, span_id)` from a W3C
trace-context header of the form `00-<32hex>-<16hex>-<2hex>`. It returns
`None` for any malformed input so callers can degrade gracefully to
empty-string field values per ADR dec-048 §Phase A.
"""

from __future__ import annotations

import pytest

from memory_mcp.correlation import parse_traceparent

# -- Reference vectors --------------------------------------------------------

# W3C trace-context spec example (https://www.w3.org/TR/trace-context/)
VALID_TRACEPARENT = "00-0af7651916cd43dd8448eb211c80319c-00f067aa0ba902b7-01"
VALID_TRACE_ID = "0af7651916cd43dd8448eb211c80319c"
VALID_SPAN_ID = "00f067aa0ba902b7"


# -- Happy path ---------------------------------------------------------------


class TestValidTraceparent:
    """Valid W3C `00-<32hex>-<16hex>-<2hex>` headers are parsed correctly."""

    def test_spec_example_returns_trace_and_span(self):
        """The W3C spec example yields the documented trace_id and span_id."""
        result = parse_traceparent(VALID_TRACEPARENT)
        assert result == (VALID_TRACE_ID, VALID_SPAN_ID)

    def test_unsampled_flag_still_parses(self):
        """A traceparent with sampled=0 still yields trace_id and span_id.

        The sampled flag governs export decisions, not parse validity.
        """
        tp = f"00-{VALID_TRACE_ID}-{VALID_SPAN_ID}-00"
        assert parse_traceparent(tp) == (VALID_TRACE_ID, VALID_SPAN_ID)

    def test_sampled_flag_ff_parses(self):
        """Any 2-hex flag value parses when the version and IDs are valid."""
        tp = f"00-{VALID_TRACE_ID}-{VALID_SPAN_ID}-ff"
        assert parse_traceparent(tp) == (VALID_TRACE_ID, VALID_SPAN_ID)

    def test_returns_tuple_of_two_strings(self):
        """Return shape is a 2-tuple of lowercase hex strings."""
        result = parse_traceparent(VALID_TRACEPARENT)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(isinstance(part, str) for part in result)

    def test_different_valid_traceparent_yields_different_ids(self):
        """Parser is not hardcoded — a different input returns different IDs."""
        tp = "00-11112222333344445555666677778888-aaaabbbbccccdddd-01"
        assert parse_traceparent(tp) == (
            "11112222333344445555666677778888",
            "aaaabbbbccccdddd",
        )


# -- Malformed inputs (table-driven) ------------------------------------------


MALFORMED_CASES = [
    # (description, value)
    ("empty-string", ""),
    ("whitespace-only", "   "),
    ("wrong-version-byte-ff", "ff-0af7651916cd43dd8448eb211c80319c-00f067aa0ba902b7-01"),
    ("wrong-version-byte-01", "01-0af7651916cd43dd8448eb211c80319c-00f067aa0ba902b7-01"),
    ("trace-id-too-short", "00-0af7651916cd43dd8448eb211c80319-00f067aa0ba902b7-01"),
    ("trace-id-too-long", "00-0af7651916cd43dd8448eb211c80319cXX-00f067aa0ba902b7-01"),
    ("span-id-too-short", "00-0af7651916cd43dd8448eb211c80319c-00f067aa0ba902b-01"),
    ("span-id-too-long", "00-0af7651916cd43dd8448eb211c80319c-00f067aa0ba902b7XX-01"),
    ("non-hex-in-trace-id", "00-Zaf7651916cd43dd8448eb211c80319c-00f067aa0ba902b7-01"),
    ("non-hex-in-span-id", "00-0af7651916cd43dd8448eb211c80319c-00f067aa0ba902bZ-01"),
    ("uppercase-hex-rejected", "00-0AF7651916CD43DD8448EB211C80319C-00F067AA0BA902B7-01"),
    ("flags-too-short", "00-0af7651916cd43dd8448eb211c80319c-00f067aa0ba902b7-1"),
    ("flags-too-long", "00-0af7651916cd43dd8448eb211c80319c-00f067aa0ba902b7-001"),
    ("truncated-no-flags", "00-0af7651916cd43dd8448eb211c80319c-00f067aa0ba902b7"),
    ("truncated-no-span", "00-0af7651916cd43dd8448eb211c80319c"),
    ("wrong-segment-count-extra", "00-0af7651916cd43dd8448eb211c80319c-00f067aa0ba902b7-01-extra"),
    ("wrong-separator", "00_0af7651916cd43dd8448eb211c80319c_00f067aa0ba902b7_01"),
    ("leading-whitespace", " 00-0af7651916cd43dd8448eb211c80319c-00f067aa0ba902b7-01"),
    ("trailing-whitespace", "00-0af7651916cd43dd8448eb211c80319c-00f067aa0ba902b7-01 "),
    ("all-zeros-trace-id", "00-00000000000000000000000000000000-00f067aa0ba902b7-01"),
    ("all-zeros-span-id", "00-0af7651916cd43dd8448eb211c80319c-0000000000000000-01"),
    ("random-junk", "not-a-traceparent"),
]


class TestMalformedTraceparent:
    """Malformed or unparseable inputs return ``None`` (no partial parse)."""

    @pytest.mark.parametrize(
        ("description", "value"),
        MALFORMED_CASES,
        ids=[case[0] for case in MALFORMED_CASES],
    )
    def test_malformed_returns_none(self, description: str, value: str):
        """Every invalid shape yields None so callers can fall back safely.

        Note: W3C §3.2.2.2/3.2.2.3 declare all-zero trace_id/span_id invalid,
        so parsers should reject them even though the hex pattern matches.
        """
        assert parse_traceparent(value) is None, (
            f"{description!r} should not parse as valid traceparent"
        )


# -- None / wrong-type handling -----------------------------------------------


class TestNonStringInput:
    """Non-string inputs are handled defensively without raising."""

    def test_none_returns_none(self):
        """Passing None yields None — matches the optional-absent contract."""
        # The contract is `value: str`; None may arrive from optional fields.
        # The parser must not raise — empty/None must both degrade to None.
        assert parse_traceparent(None) is None  # type: ignore[arg-type]


# -- Sampled flag variants ----------------------------------------------------


SAMPLED_FLAG_VARIANTS = [
    ("sampled-on-01", "01"),
    ("sampled-off-00", "00"),
    ("all-bits-ff", "ff"),
    ("random-flag-a0", "a0"),
]


class TestSampledFlagVariants:
    """The flag byte does not affect parse success for valid hex flags."""

    @pytest.mark.parametrize(
        ("description", "flag"),
        SAMPLED_FLAG_VARIANTS,
        ids=[case[0] for case in SAMPLED_FLAG_VARIANTS],
    )
    def test_flag_variant_parses(self, description: str, flag: str):
        tp = f"00-{VALID_TRACE_ID}-{VALID_SPAN_ID}-{flag}"
        assert parse_traceparent(tp) == (VALID_TRACE_ID, VALID_SPAN_ID)
