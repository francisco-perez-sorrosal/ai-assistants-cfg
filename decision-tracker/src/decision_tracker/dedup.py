"""Deduplication of decision candidates against existing entries."""

from __future__ import annotations

import re

from decision_tracker.schema import Decision


def _normalize(text: str) -> str:
    """Normalize text for comparison: lowercase, strip, collapse whitespace."""
    stripped = text.strip().lower()
    return re.sub(r"\s+", " ", stripped)


def deduplicate(candidates: list[Decision], existing: list[Decision]) -> list[Decision]:
    """Filter candidates that exactly match an existing decision's normalized text.

    Returns only candidates whose normalized decision text does not appear
    in the existing entries.
    """
    existing_texts = {_normalize(d.decision) for d in existing}
    return [c for c in candidates if _normalize(c.decision) not in existing_texts]
