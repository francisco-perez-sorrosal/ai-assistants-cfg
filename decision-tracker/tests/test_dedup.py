"""Tests for decision_tracker.dedup — validates deduplication logic."""

from __future__ import annotations

from decision_tracker.dedup import deduplicate
from decision_tracker.schema import Decision

MINIMAL_FIELDS = {
    "status": "documented",
    "category": "implementation",
    "made_by": "agent",
    "source": "agent",
}


def _make_decision(text: str) -> Decision:
    """Create a Decision with only the required fields plus decision text."""
    return Decision(decision=text, **MINIMAL_FIELDS)


class TestDeduplicate:
    def test_no_existing_returns_all(self):
        candidates = [_make_decision("Use Redis"), _make_decision("Use Postgres")]
        result = deduplicate(candidates, existing=[])
        assert len(result) == 2

    def test_exact_match_filtered(self):
        candidates = [_make_decision("Use Redis")]
        existing = [_make_decision("Use Redis")]
        result = deduplicate(candidates, existing)
        assert result == []

    def test_case_insensitive(self):
        candidates = [_make_decision("Use Redis")]
        existing = [_make_decision("use redis")]
        result = deduplicate(candidates, existing)
        assert result == []

    def test_whitespace_normalized(self):
        candidates = [_make_decision(" Use Redis ")]
        existing = [_make_decision("Use Redis")]
        result = deduplicate(candidates, existing)
        assert result == []

    def test_multi_space_normalized(self):
        candidates = [_make_decision("Use  Redis")]
        existing = [_make_decision("Use Redis")]
        result = deduplicate(candidates, existing)
        assert result == []

    def test_different_decisions_kept(self):
        candidates = [_make_decision("Use Redis")]
        existing = [_make_decision("Use Memcached")]
        result = deduplicate(candidates, existing)
        assert len(result) == 1
        assert result[0].decision == "Use Redis"

    def test_empty_candidates_returns_empty(self):
        existing = [_make_decision("Use Redis")]
        result = deduplicate(candidates=[], existing=existing)
        assert result == []

    def test_multiple_matches(self):
        candidates = [
            _make_decision("Use Redis"),
            _make_decision("Use Postgres"),
            _make_decision("Use Docker"),
        ]
        existing = [
            _make_decision("Use Redis"),
            _make_decision("Use Docker"),
        ]
        result = deduplicate(candidates, existing)
        assert len(result) == 1
        assert result[0].decision == "Use Postgres"
