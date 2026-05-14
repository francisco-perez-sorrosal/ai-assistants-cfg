"""Behavioral tests for the VERIFIER_FINDINGS.md seven-section schema.

Approach A — schema-validation tests against a synthesized fixture file.
The fixture (tests/fixtures/verifier_findings_complete.md) models what the
main agent would produce when writing a VERIFIER_FINDINGS.md into a rework
worktree.  Tests are RED until the fixture exists AND matches the required schema.

These tests validate the receiver side of Phase 12.5 (what the architect / planner
reads).  No production module import is required — all assertions are structural
reads of the markdown fixture.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"
FINDINGS_FIXTURE = FIXTURES / "verifier_findings_complete.md"

# The seven sections in the order they must appear (case-sensitive heading match).
REQUIRED_SECTIONS = [
    "Problem",
    "Scope",
    "Evidence",
    "Success Criteria",
    "Ledger Links",
    "Suggested Tier",
    "Provenance",
]

CONFIDENCE_VALUES = {"high", "medium", "low"}


def _section_order(text: str) -> list[str]:
    """Return the list of top-level (##) heading titles found in the text."""
    return re.findall(r"^##\s+(.+)$", text, re.MULTILINE)


def _section_body(text: str, heading: str) -> str:
    """Return the body text between a ## heading and the next ## heading."""
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$(.+?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# Test: all seven sections present in required order
# ---------------------------------------------------------------------------


def test_seven_sections_present_in_order():
    """A valid VERIFIER_FINDINGS.md must contain exactly the seven required
    top-level sections in the prescribed order."""
    assert FINDINGS_FIXTURE.exists(), (
        f"Fixture {FINDINGS_FIXTURE.name} not found; "
        "verifier Phase 12.5 must produce VERIFIER_FINDINGS.md with seven required sections"
    )
    text = FINDINGS_FIXTURE.read_text(encoding="utf-8")
    found = _section_order(text)

    for section in REQUIRED_SECTIONS:
        assert section in found, (
            f"Required section '## {section}' missing from VERIFIER_FINDINGS.md; "
            f"found sections: {found}"
        )

    # Verify ordering: each required section must appear after the previous one
    indices = [found.index(s) for s in REQUIRED_SECTIONS if s in found]
    assert indices == sorted(indices), (
        f"Required sections are out of order; expected {REQUIRED_SECTIONS}, "
        f"found order: {[found[i] for i in indices]}"
    )


# ---------------------------------------------------------------------------
# Test: Provenance section contains a Rework ID line
# ---------------------------------------------------------------------------


def test_provenance_contains_rework_id():
    """The ## Provenance section must contain a 'Rework ID:' line matching rw-<hash>."""
    assert FINDINGS_FIXTURE.exists(), f"Fixture {FINDINGS_FIXTURE.name} not found"
    text = FINDINGS_FIXTURE.read_text(encoding="utf-8")
    provenance = _section_body(text, "Provenance")
    assert provenance, "## Provenance section must not be empty"

    rework_id_match = re.search(r"Rework ID:.*?(rw-[0-9a-f]{8})", provenance)
    assert rework_id_match, (
        f"## Provenance section must contain a 'Rework ID: rw-<8-hex>' line; "
        f"section body:\n{provenance}"
    )


# ---------------------------------------------------------------------------
# Test: Evidence references only the cluster's finding anchors
# ---------------------------------------------------------------------------


def test_evidence_filtered_subset_of_report():
    """The ## Evidence section must reference only the cluster's finding anchors,
    not unrelated findings from the parent report.

    The fixture clusters findings #fail-1 and #fail-2.  The evidence section
    must reference these and must NOT reference #fail-3, #warn-1, #warn-2 (which
    belong to a different cluster in the parent report).
    """
    assert FINDINGS_FIXTURE.exists(), f"Fixture {FINDINGS_FIXTURE.name} not found"
    text = FINDINGS_FIXTURE.read_text(encoding="utf-8")
    evidence = _section_body(text, "Evidence")
    assert evidence, "## Evidence section must not be empty"

    # The fixture's cluster is #fail-1, #fail-2 only
    cluster_refs = {"#fail-1", "#fail-2"}
    out_of_cluster_refs = {"#fail-3", "#warn-1", "#warn-2", "#warn-3"}

    for ref in cluster_refs:
        assert ref in evidence, (
            f"Expected cluster finding ref {ref!r} in ## Evidence section; "
            f"evidence body:\n{evidence}"
        )
    for ref in out_of_cluster_refs:
        assert ref not in evidence, (
            f"Out-of-cluster finding ref {ref!r} must not appear in ## Evidence; "
            "evidence must be a filtered subset, not a full copy of the report"
        )


# ---------------------------------------------------------------------------
# Test: Success Criteria has at least one checkable bullet
# ---------------------------------------------------------------------------


def test_success_criteria_present_and_actionable():
    """The ## Success Criteria section must contain at least one checkbox bullet
    describing a checkable outcome (e.g., '- [ ] ...' or '- [x] ...')."""
    assert FINDINGS_FIXTURE.exists(), f"Fixture {FINDINGS_FIXTURE.name} not found"
    text = FINDINGS_FIXTURE.read_text(encoding="utf-8")
    criteria = _section_body(text, "Success Criteria")
    assert criteria, "## Success Criteria section must not be empty"

    checkboxes = re.findall(r"^- \[[ x]\] .+", criteria, re.MULTILINE)
    assert checkboxes, (
        f"## Success Criteria must contain at least one '- [ ] ...' checkbox bullet; "
        f"section body:\n{criteria}"
    )


# ---------------------------------------------------------------------------
# Test: confidence field is constrained to allowed enum values
# ---------------------------------------------------------------------------


def test_confidence_enum_constrained():
    """The Provenance section must contain a 'Verifier confidence:' field whose
    value is one of {high, medium, low}."""
    assert FINDINGS_FIXTURE.exists(), f"Fixture {FINDINGS_FIXTURE.name} not found"
    text = FINDINGS_FIXTURE.read_text(encoding="utf-8")
    provenance = _section_body(text, "Provenance")
    assert provenance, "## Provenance section must not be empty"

    confidence_match = re.search(r"Verifier confidence:\s*`?(\w+)`?", provenance)
    assert confidence_match, (
        f"## Provenance must contain a 'Verifier confidence: <value>' line; "
        f"section body:\n{provenance}"
    )
    value = confidence_match.group(1).lower()
    assert value in CONFIDENCE_VALUES, (
        f"Verifier confidence {value!r} must be one of {CONFIDENCE_VALUES}; "
        f"section body:\n{provenance}"
    )
