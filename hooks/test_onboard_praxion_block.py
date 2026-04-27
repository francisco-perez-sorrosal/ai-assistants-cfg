"""Tests for the §Praxion Process canonical block in onboard-project.md and new-project.md.

Behavioral coverage:
  - The §Praxion Process Block section exists in commands/onboard-project.md
  - The §Praxion Process Block section exists in commands/new-project.md
  - The block is byte-identical between both command files
  - Phase 6 in both commands references four blocks (including the new one)
  - The block contains required structural elements (principle, rule-inheritance
    corollary, trivial-vs-non-trivial threshold, orchestrator delegation obligation)
  - The block contains no .ai-state/ or .ai-work/ identifiers (shipped artifact isolation)
  - The block stays under the ~250-token budget (bytes/3.6 < 250)
  - The idempotency predicate prevents duplicate insertion on a second Phase 6 run

These tests are expected to FAIL (RED) until the §Praxion Process block is
present in both command files.
"""

from __future__ import annotations

import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
ONBOARD_PATH = REPO_ROOT / "commands" / "onboard-project.md"
NEW_PROJECT_PATH = REPO_ROOT / "commands" / "new-project.md"

# The canonical heading that identifies the block section in command files.
# The block itself (when injected into user CLAUDE.md) uses ## Praxion Process.
BLOCK_SECTION_HEADING = "## §Praxion Process Block"

# The heading that the idempotency predicate checks for in the user's CLAUDE.md.
CLAUDE_MD_HEADING = "## Praxion Process"

# Token budget ceiling (conservative Praxion convention: bytes / 3.6)
TOKEN_BUDGET = 250


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_command_file(path: Path) -> str:
    """Read a command file, asserting it exists."""
    assert path.exists(), f"Command file not found: {path}"
    return path.read_text(encoding="utf-8")


def _extract_block_section(content: str) -> str:
    """Extract the content of the §Praxion Process Block section from a command file.

    The section starts at '## §Praxion Process Block' and ends at the next
    top-level '## ' heading (or end of file).

    Returns the extracted section text (including the heading line).
    Raises AssertionError if the section is absent.
    """
    # Find the heading
    match = re.search(r"^## §Praxion Process Block\b.*$", content, re.MULTILINE)
    assert match is not None, (
        f"Heading '{BLOCK_SECTION_HEADING}' not found in content "
        f"(first 200 chars: {content[:200]!r})"
    )
    start = match.start()

    # Find where the next canonical-block section heading begins (or EOF).
    # Canonical-block sections all use the `## §` prefix; matching plain `## `
    # would falsely terminate at the inner injectable `## Praxion Process` heading.
    next_heading = re.search(r"^## §", content[match.end() :], re.MULTILINE)
    if next_heading is None:
        end = len(content)
    else:
        end = match.end() + next_heading.start()

    return content[start:end].rstrip()


def _extract_inline_block(content: str) -> str:
    """Extract the prose block that will be injected into user CLAUDE.md.

    The block starts at '## Praxion Process' and ends at the next '## ' heading
    or end of the §Praxion Process Block section. Returns just the block prose.
    """
    section = _extract_block_section(content)
    # Within the section, the injectable block starts at ## Praxion Process
    match = re.search(r"^## Praxion Process\b.*$", section, re.MULTILINE)
    assert match is not None, (
        "'## Praxion Process' not found inside §Praxion Process Block section"
    )
    start = match.start()

    next_heading = re.search(r"^## ", section[match.end() :], re.MULTILINE)
    if next_heading is None:
        end = len(section)
    else:
        end = match.end() + next_heading.start()

    return section[start:end].rstrip()


# ---------------------------------------------------------------------------
# Phase 1: RED skeleton assertions — block presence
# These are the first-run failing assertions. They establish the RED state.
# ---------------------------------------------------------------------------


def test_praxion_process_block_section_exists_in_onboard_project():
    """onboard-project.md must contain the §Praxion Process Block section heading."""
    content = _read_command_file(ONBOARD_PATH)
    assert BLOCK_SECTION_HEADING in content, (
        f"'{BLOCK_SECTION_HEADING}' not found in {ONBOARD_PATH.name}. "
        "The implementer must add the canonical block section before this test passes."
    )


def test_praxion_process_block_section_exists_in_new_project():
    """new-project.md must contain the §Praxion Process Block section heading."""
    content = _read_command_file(NEW_PROJECT_PATH)
    assert BLOCK_SECTION_HEADING in content, (
        f"'{BLOCK_SECTION_HEADING}' not found in {NEW_PROJECT_PATH.name}. "
        "The implementer must mirror the canonical block before this test passes."
    )


def test_claude_md_heading_present_in_onboard_project_block():
    """The §Praxion Process Block section must contain the '## Praxion Process' heading."""
    content = _read_command_file(ONBOARD_PATH)
    section = _extract_block_section(content)
    assert CLAUDE_MD_HEADING in section, (
        f"'## Praxion Process' heading not found inside §Praxion Process Block section "
        f"in {ONBOARD_PATH.name}."
    )


def test_claude_md_heading_present_in_new_project_block():
    """The §Praxion Process Block section in new-project.md must contain '## Praxion Process'."""
    content = _read_command_file(NEW_PROJECT_PATH)
    section = _extract_block_section(content)
    assert CLAUDE_MD_HEADING in section, (
        f"'## Praxion Process' heading not found inside §Praxion Process Block section "
        f"in {NEW_PROJECT_PATH.name}."
    )


# ---------------------------------------------------------------------------
# Phase 2: Byte-identical mirror constraint
# ---------------------------------------------------------------------------


def test_praxion_process_block_is_byte_identical_between_both_command_files():
    """The §Praxion Process Block section must be byte-identical in both command files.

    This is the load-bearing byte-identical-mirror constraint: both commands are
    the canonical source of truth for the block injected into user CLAUDE.md files.
    Any drift between the two files means users onboarded via different paths
    receive different standing instructions.
    """
    onboard_content = _read_command_file(ONBOARD_PATH)
    new_project_content = _read_command_file(NEW_PROJECT_PATH)

    onboard_block = _extract_block_section(onboard_content)
    new_project_block = _extract_block_section(new_project_content)

    assert onboard_block == new_project_block, (
        "§Praxion Process Block is NOT byte-identical between command files.\n"
        f"onboard-project.md block ({len(onboard_block)} chars):\n{onboard_block[:300]!r}\n\n"
        f"new-project.md block ({len(new_project_block)} chars):\n{new_project_block[:300]!r}"
    )


# ---------------------------------------------------------------------------
# Phase 3: Block placement — after §Behavioral Contract
# ---------------------------------------------------------------------------


def test_praxion_process_block_appears_after_behavioral_contract_in_onboard_project():
    """The §Praxion Process Block must appear after §Behavioral Contract Block in onboard-project.md."""
    content = _read_command_file(ONBOARD_PATH)

    behavioral_contract_pos = content.find("## §Behavioral Contract Block")
    praxion_process_pos = content.find(BLOCK_SECTION_HEADING)

    assert behavioral_contract_pos != -1, (
        "'## §Behavioral Contract Block' not found in onboard-project.md"
    )
    assert praxion_process_pos != -1, (
        f"'{BLOCK_SECTION_HEADING}' not found in onboard-project.md"
    )
    assert praxion_process_pos > behavioral_contract_pos, (
        f"'{BLOCK_SECTION_HEADING}' must appear after '## §Behavioral Contract Block'. "
        f"Behavioral contract at pos {behavioral_contract_pos}, "
        f"Praxion Process at pos {praxion_process_pos}."
    )


def test_phase_6_references_four_blocks_in_onboard_project():
    """Phase 6 gate message or action text must reference four blocks (not three)."""
    content = _read_command_file(ONBOARD_PATH)
    # Find the Phase 6 section
    phase6_match = re.search(r"^## §Phase 6.*$", content, re.MULTILINE)
    assert phase6_match is not None, "§Phase 6 section not found in onboard-project.md"

    # Find the next ## section after Phase 6 to scope our search
    next_section = re.search(
        r"^## §Phase 7", content[phase6_match.end() :], re.MULTILINE
    )
    if next_section:
        phase6_text = content[
            phase6_match.start() : phase6_match.end() + next_section.start()
        ]
    else:
        phase6_text = content[phase6_match.start() :]

    # Phase 6 should reference "Praxion Process" as one of the blocks
    assert "Praxion Process" in phase6_text, (
        "Phase 6 section in onboard-project.md does not mention 'Praxion Process'. "
        "The phase description must be updated to reference four blocks."
    )


def test_phase_6_references_four_blocks_in_new_project():
    """Phase 6 equivalent in new-project.md must also reference the Praxion Process block."""
    content = _read_command_file(NEW_PROJECT_PATH)
    # Find any phase 6 reference in new-project.md
    assert "Praxion Process" in content, (
        "new-project.md does not mention 'Praxion Process' — "
        "the mirrored block reference is missing."
    )


# ---------------------------------------------------------------------------
# Phase 4: Block content structural requirements
# ---------------------------------------------------------------------------


def test_praxion_process_block_contains_principle_language():
    """The block prose must reference the principle (Praxion's tier-driven process)."""
    content = _read_command_file(ONBOARD_PATH)
    block = _extract_inline_block(content)
    # The principle must be nameable — look for tier-selector or pipeline reference
    tier_or_pipeline = re.search(
        r"tier.{0,30}(selector|pipeline)|pipeline.{0,20}tier", block, re.IGNORECASE
    )
    assert tier_or_pipeline is not None, (
        "Block prose does not reference the tier selector or pipeline principle. "
        f"Block content:\n{block}"
    )


def test_praxion_process_block_contains_rule_inheritance_corollary():
    """The block prose must reference rule-inheritance or delegation to subagents."""
    content = _read_command_file(ONBOARD_PATH)
    block = _extract_inline_block(content)
    # Rule-inheritance corollary: orchestrator carries contract into delegations
    inheritance_ref = re.search(
        r"(subagent|delegation|host.native|inject|inherit|behavioral contract)",
        block,
        re.IGNORECASE,
    )
    assert inheritance_ref is not None, (
        "Block prose does not reference rule-inheritance corollary "
        "(subagent injection, delegation, or behavioral contract carry-forward). "
        f"Block content:\n{block}"
    )


def test_praxion_process_block_contains_threshold_reference():
    """The block prose must reference the trivial-vs-non-trivial threshold."""
    content = _read_command_file(ONBOARD_PATH)
    block = _extract_inline_block(content)
    threshold_ref = re.search(
        r"(trivial|non.trivial|threshold|simple|direct.tier|lightweight)",
        block,
        re.IGNORECASE,
    )
    assert threshold_ref is not None, (
        "Block prose does not reference the trivial-vs-non-trivial threshold. "
        f"Block content:\n{block}"
    )


def test_praxion_process_block_contains_orchestrator_obligation():
    """The block prose must state the orchestrator's obligation to carry the contract."""
    content = _read_command_file(ONBOARD_PATH)
    block = _extract_inline_block(content)
    obligation_ref = re.search(
        r"(orchestrat|delegation|delegation prompt|carry|include|pass)",
        block,
        re.IGNORECASE,
    )
    assert obligation_ref is not None, (
        "Block prose does not state the orchestrator delegation obligation. "
        f"Block content:\n{block}"
    )


# ---------------------------------------------------------------------------
# Phase 5: Shipped artifact isolation
# ---------------------------------------------------------------------------


def test_praxion_process_block_contains_no_ai_state_identifiers():
    """The block prose must not reference .ai-state/ entries (dec-NNN, SPEC_*, etc.)."""
    content = _read_command_file(ONBOARD_PATH)
    block = _extract_inline_block(content)

    forbidden_patterns = [
        r"\.ai-state/",
        r"\.ai-work/",
        r"dec-\d+",
        r"SPEC_\w+_\d{4}-\d{2}-\d{2}",
        r"SENTINEL_REPORT_\d{4}",
    ]
    for pattern in forbidden_patterns:
        match = re.search(pattern, block)
        assert match is None, (
            f"Block prose contains a forbidden shipped-artifact reference "
            f"matching '{pattern}': {match.group()!r}. "
            "The block must not reference .ai-state/ or .ai-work/ entries."
        )


def test_praxion_process_block_contains_no_ai_state_identifiers_in_new_project():
    """new-project.md block must also contain no .ai-state/ references."""
    content = _read_command_file(NEW_PROJECT_PATH)
    block = _extract_inline_block(content)

    forbidden_patterns = [
        r"\.ai-state/",
        r"\.ai-work/",
        r"dec-\d+",
        r"SPEC_\w+_\d{4}-\d{2}-\d{2}",
    ]
    for pattern in forbidden_patterns:
        match = re.search(pattern, block)
        assert match is None, (
            f"new-project.md block prose contains forbidden reference "
            f"matching '{pattern}': {match.group()!r}."
        )


# ---------------------------------------------------------------------------
# Phase 6: Token budget
# ---------------------------------------------------------------------------


def test_praxion_process_block_stays_within_token_budget():
    """The injectable block must be under ~250 tokens (bytes/3.6 conservative estimate)."""
    content = _read_command_file(ONBOARD_PATH)
    block = _extract_inline_block(content)
    block_bytes = len(block.encode("utf-8"))
    conservative_tokens = block_bytes / 3.6
    assert conservative_tokens < TOKEN_BUDGET, (
        f"Block exceeds token budget. "
        f"Block is {block_bytes} bytes ({conservative_tokens:.1f} tokens by bytes/3.6 estimate). "
        f"Budget is {TOKEN_BUDGET} tokens. "
        "Trim the block prose before merging."
    )


# ---------------------------------------------------------------------------
# Phase 7: Idempotency simulation
# ---------------------------------------------------------------------------


def test_idempotency_predicate_heading_is_in_command_files(tmp_path):
    """The idempotency predicate heading '## Praxion Process' used in Phase 6 must be
    present in the command file, so the re-run skip logic works correctly.

    This test simulates the idempotency check: if CLAUDE.md already contains
    '## Praxion Process', a second Phase 6 run must NOT re-append the block.
    The test verifies the heading used by the predicate matches the heading in
    the block — preventing the duplicate-insertion scenario.
    """
    content = _read_command_file(ONBOARD_PATH)
    block = _extract_inline_block(content)

    # The block must start with the heading that the predicate checks
    assert block.startswith(CLAUDE_MD_HEADING), (
        f"The injectable block does not start with '{CLAUDE_MD_HEADING}'. "
        "The idempotency predicate checks for this heading in CLAUDE.md. "
        f"Block starts with: {block[:80]!r}"
    )

    # Simulate: write the block to a temp CLAUDE.md
    fixture_claude_md = tmp_path / "CLAUDE.md"
    fixture_claude_md.write_text(f"\n\n{block}\n", encoding="utf-8")

    # Simulate idempotency check: grep-equivalent for the heading
    claude_md_content = fixture_claude_md.read_text(encoding="utf-8")
    heading_present = CLAUDE_MD_HEADING in claude_md_content
    assert heading_present, (
        "After writing the block to CLAUDE.md, the idempotency heading was not found. "
        "This means a second Phase 6 run would re-append the block (duplicating it)."
    )


def test_second_phase6_run_produces_no_duplicate_when_block_already_present(tmp_path):
    """Simulates two Phase 6 runs: the second run must detect the existing heading
    and skip the append, leaving CLAUDE.md unchanged.

    This tests the predicate logic: heading-present → skip.
    """
    content = _read_command_file(ONBOARD_PATH)
    block = _extract_inline_block(content)

    # First run: CLAUDE.md has no Praxion Process block
    fixture_claude_md = tmp_path / "CLAUDE.md"
    fixture_claude_md.write_text(
        "# Project\n\n## Behavioral Contract\n\nContract text.\n", encoding="utf-8"
    )

    # Simulate Phase 6 first run (append if heading absent)
    claude_content = fixture_claude_md.read_text(encoding="utf-8")
    if CLAUDE_MD_HEADING not in claude_content:
        fixture_claude_md.write_text(claude_content + f"\n{block}\n", encoding="utf-8")

    after_first_run = fixture_claude_md.read_text(encoding="utf-8")
    first_run_count = after_first_run.count(CLAUDE_MD_HEADING)
    assert first_run_count == 1, (
        f"After first Phase 6 run, expected 1 occurrence of '{CLAUDE_MD_HEADING}', "
        f"got {first_run_count}."
    )

    # Simulate Phase 6 second run (should be a no-op because heading is present)
    claude_content = fixture_claude_md.read_text(encoding="utf-8")
    if CLAUDE_MD_HEADING not in claude_content:
        fixture_claude_md.write_text(claude_content + f"\n{block}\n", encoding="utf-8")

    after_second_run = fixture_claude_md.read_text(encoding="utf-8")
    second_run_count = after_second_run.count(CLAUDE_MD_HEADING)
    assert second_run_count == 1, (
        f"After second Phase 6 run, '{CLAUDE_MD_HEADING}' appears {second_run_count} times "
        f"(expected 1 — idempotency predicate should have suppressed the second append)."
    )

    # File content must be identical after the second run (zero diff)
    assert after_first_run == after_second_run, (
        "CLAUDE.md changed between first and second Phase 6 run — idempotency violated."
    )
