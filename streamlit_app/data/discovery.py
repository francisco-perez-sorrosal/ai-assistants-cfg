"""Discovery layer for the Praxion Pipeline Dashboard.

Pure read-only filesystem inspection. No caching, no Streamlit imports.
Stateful artifacts live in <root>/.ai-state/ ; ephemeral workshops live in
<root>/.ai-work/<task-slug>/ .

All functions:
- Are pure (no caching, no side effects).
- Return Optional[Path] (None if absent) or list[Path] (empty if absent).
- Never raise on missing files; absence is a valid result.
- DO raise FileNotFoundError if ``root`` itself does not exist.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Filename patterns
# ---------------------------------------------------------------------------

_FINALIZED_ADR = re.compile(r"^\d{3}-[a-z0-9-]+\.md$")
_SENTINEL_REPORT = re.compile(
    r"^SENTINEL_REPORT_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.md$"
)
_METRICS_REPORT_MD = re.compile(
    r"^METRICS_REPORT_\d{4}-\d{2}-\d{2}(?:_\d{2}-\d{2}-\d{2})?\.md$"
)
_METRICS_REPORT_JSON = re.compile(
    r"^METRICS_REPORT_\d{4}-\d{2}-\d{2}(?:_\d{2}-\d{2}-\d{2})?\.json$"
)
_IDEA_LEDGER = re.compile(r"^IDEA_LEDGER_\d{4}-\d{2}-\d{2}.*\.md$")
_SPEC = re.compile(r"^SPEC_.*_\d{4}-\d{2}-\d{2}\.md$")

# Canonical workshop artifact filenames (from agent-intermediate-documents.md).
WORKSHOP_ARTIFACT_NAMES = frozenset(
    {
        "SYSTEMS_PLAN.md",
        "IMPLEMENTATION_PLAN.md",
        "WIP.md",
        "LEARNINGS.md",
        "TEST_RESULTS.md",
        "traceability.yml",
        "VERIFICATION_REPORT.md",
        "PROGRESS.md",
        "RESEARCH_FINDINGS.md",
        "IDEA_PROPOSAL.md",
        "CONTEXT_REVIEW.md",
        "SPEC_DELTA.md",
        "SKILL_GENESIS_REPORT.md",
    }
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _require_root(root: Path) -> None:
    """Raise FileNotFoundError if *root* does not exist."""
    if not root.exists():
        raise FileNotFoundError(f"Project root does not exist: {root}")


def _glob_sorted_desc(directory: Path, pattern: str) -> list[Path]:
    """Return files matching *pattern* inside *directory*, newest filename first.

    Uses lexicographic descending order — valid for timestamp-in-filename
    artifacts (SENTINEL_REPORT_, METRICS_REPORT_, IDEA_LEDGER_, SPEC_).
    Returns [] if the directory is absent.
    """
    if not directory.is_dir():
        return []
    return sorted(directory.glob(pattern), key=lambda p: p.name, reverse=True)


def _glob_sorted_asc(directory: Path, pattern: str) -> list[Path]:
    """Return files matching *pattern* inside *directory*, ascending by name.

    Returns [] if the directory is absent.
    """
    if not directory.is_dir():
        return []
    return sorted(directory.glob(pattern), key=lambda p: p.name)


# ---------------------------------------------------------------------------
# Persistent (.ai-state/) — stateful info
# ---------------------------------------------------------------------------


def find_architecture_md(root: Path) -> Optional[Path]:
    """Return path to ``.ai-state/ARCHITECTURE.md``, or None if absent."""
    _require_root(root)
    candidate = root / ".ai-state" / "ARCHITECTURE.md"
    return candidate if candidate.is_file() else None


def find_system_deployment(root: Path) -> Optional[Path]:
    """Return path to ``.ai-state/SYSTEM_DEPLOYMENT.md``, or None if absent."""
    _require_root(root)
    candidate = root / ".ai-state" / "SYSTEM_DEPLOYMENT.md"
    return candidate if candidate.is_file() else None


def find_test_topology(root: Path) -> Optional[Path]:
    """Return path to ``.ai-state/TEST_TOPOLOGY.md``, or None if absent."""
    _require_root(root)
    candidate = root / ".ai-state" / "TEST_TOPOLOGY.md"
    return candidate if candidate.is_file() else None


def find_calibration_log(root: Path) -> Optional[Path]:
    """Return path to ``.ai-state/calibration_log.md``, or None if absent."""
    _require_root(root)
    candidate = root / ".ai-state" / "calibration_log.md"
    return candidate if candidate.is_file() else None


def find_tech_debt_active(root: Path) -> Optional[Path]:
    """Return path to ``.ai-state/TECH_DEBT_LEDGER.md``, or None if absent."""
    _require_root(root)
    candidate = root / ".ai-state" / "TECH_DEBT_LEDGER.md"
    return candidate if candidate.is_file() else None


def find_tech_debt_resolved(root: Path) -> Optional[Path]:
    """Return path to ``.ai-state/TECH_DEBT_RESOLVED.md``, or None if absent."""
    _require_root(root)
    candidate = root / ".ai-state" / "TECH_DEBT_RESOLVED.md"
    return candidate if candidate.is_file() else None


def find_decisions_index(root: Path) -> Optional[Path]:
    """Return path to ``.ai-state/decisions/DECISIONS_INDEX.md``, or None."""
    _require_root(root)
    candidate = root / ".ai-state" / "decisions" / "DECISIONS_INDEX.md"
    return candidate if candidate.is_file() else None


def list_adrs_finalized(root: Path) -> list[Path]:
    r"""Return finalized ADRs (``decisions/<NNN>-<slug>.md``), NNN-sorted ASC.

    Only files directly inside ``.ai-state/decisions/`` whose names match
    ``^\d{3}-[a-z0-9-]+\.md$`` are returned.  The ``drafts/`` sub-directory
    is excluded.
    """
    _require_root(root)
    decisions_dir = root / ".ai-state" / "decisions"
    if not decisions_dir.is_dir():
        return []
    candidates = [
        p
        for p in decisions_dir.iterdir()
        if p.is_file() and _FINALIZED_ADR.match(p.name)
    ]
    return sorted(candidates, key=lambda p: p.name)


def list_adrs_drafts(root: Path) -> list[Path]:
    """Return draft ADRs from ``decisions/drafts/*.md``, alpha-sorted ASC."""
    _require_root(root)
    drafts_dir = root / ".ai-state" / "decisions" / "drafts"
    return _glob_sorted_asc(drafts_dir, "*.md")


def list_sentinel_reports(root: Path) -> list[Path]:
    """Return ``SENTINEL_REPORT_*.md`` paths, newest filename first."""
    _require_root(root)
    reports_dir = root / ".ai-state" / "sentinel_reports"
    if not reports_dir.is_dir():
        return []
    candidates = [
        p
        for p in reports_dir.iterdir()
        if p.is_file() and _SENTINEL_REPORT.match(p.name)
    ]
    return sorted(candidates, key=lambda p: p.name, reverse=True)


def find_sentinel_log(root: Path) -> Optional[Path]:
    """Return path to ``sentinel_reports/SENTINEL_LOG.md``, or None."""
    _require_root(root)
    candidate = root / ".ai-state" / "sentinel_reports" / "SENTINEL_LOG.md"
    return candidate if candidate.is_file() else None


def list_metrics_reports_md(root: Path) -> list[Path]:
    """Return ``METRICS_REPORT_*.md`` paths, newest filename first."""
    _require_root(root)
    reports_dir = root / ".ai-state" / "metrics_reports"
    if not reports_dir.is_dir():
        return []
    candidates = [
        p
        for p in reports_dir.iterdir()
        if p.is_file() and _METRICS_REPORT_MD.match(p.name)
    ]
    return sorted(candidates, key=lambda p: p.name, reverse=True)


def list_metrics_reports_json(root: Path) -> list[Path]:
    """Return ``METRICS_REPORT_*.json`` paths, newest filename first."""
    _require_root(root)
    reports_dir = root / ".ai-state" / "metrics_reports"
    if not reports_dir.is_dir():
        return []
    candidates = [
        p
        for p in reports_dir.iterdir()
        if p.is_file() and _METRICS_REPORT_JSON.match(p.name)
    ]
    return sorted(candidates, key=lambda p: p.name, reverse=True)


def find_metrics_log(root: Path) -> Optional[Path]:
    """Return path to ``metrics_reports/METRICS_LOG.md``, or None."""
    _require_root(root)
    candidate = root / ".ai-state" / "metrics_reports" / "METRICS_LOG.md"
    return candidate if candidate.is_file() else None


def list_idea_ledgers(root: Path) -> list[Path]:
    """Return ``IDEA_LEDGER_*.md`` paths, newest filename first."""
    _require_root(root)
    ledgers_dir = root / ".ai-state" / "idea_ledgers"
    if not ledgers_dir.is_dir():
        return []
    candidates = [
        p for p in ledgers_dir.iterdir() if p.is_file() and _IDEA_LEDGER.match(p.name)
    ]
    return sorted(candidates, key=lambda p: p.name, reverse=True)


def list_specs(root: Path) -> list[Path]:
    """Return archived spec files (``SPEC_*_YYYY-MM-DD.md``), newest first."""
    _require_root(root)
    specs_dir = root / ".ai-state" / "specs"
    if not specs_dir.is_dir():
        return []
    candidates = [p for p in specs_dir.iterdir() if p.is_file() and _SPEC.match(p.name)]
    return sorted(candidates, key=lambda p: p.name, reverse=True)


# ---------------------------------------------------------------------------
# Ephemeral (.ai-work/<task-slug>/) — workshops
# ---------------------------------------------------------------------------


def list_active_workshops(root: Path) -> list[Path]:
    """Return ``.ai-work/<task-slug>/`` directories, newest mtime first.

    Skips non-directory entries inside ``.ai-work/``.
    Returns [] if ``.ai-work/`` is absent.
    """
    _require_root(root)
    ai_work = root / ".ai-work"
    if not ai_work.is_dir():
        return []
    dirs = [p for p in ai_work.iterdir() if p.is_dir()]
    return sorted(dirs, key=lambda p: os.stat(p).st_mtime, reverse=True)


def find_workshop_artifact(workshop_dir: Path, name: str) -> Optional[Path]:
    """Return ``workshop_dir / name`` if it exists, else None.

    *name* should be one of the canonical workshop artifact filenames defined
    in ``WORKSHOP_ARTIFACT_NAMES``.
    """
    candidate = workshop_dir / name
    return candidate if candidate.is_file() else None


# ---------------------------------------------------------------------------
# Project root level
# ---------------------------------------------------------------------------


def find_roadmap(root: Path) -> Optional[Path]:
    """Return ``<root>/ROADMAP.md`` if it exists, else None."""
    _require_root(root)
    candidate = root / "ROADMAP.md"
    return candidate if candidate.is_file() else None


def find_developer_architecture(root: Path) -> Optional[Path]:
    """Return ``<root>/docs/architecture.md`` if it exists, else None."""
    _require_root(root)
    candidate = root / "docs" / "architecture.md"
    return candidate if candidate.is_file() else None


def list_likec4_svgs(root: Path) -> list[Path]:
    """Return all ``*.svg`` files under ``<root>/docs/diagrams/``, alpha-sorted."""
    _require_root(root)
    diagrams_dir = root / "docs" / "diagrams"
    if not diagrams_dir.is_dir():
        return []
    return sorted(diagrams_dir.rglob("*.svg"), key=lambda p: str(p))


def list_likec4_sources(root: Path) -> list[Path]:
    """Return all ``*.c4`` files under ``<root>/docs/diagrams/``, alpha-sorted."""
    _require_root(root)
    diagrams_dir = root / "docs" / "diagrams"
    if not diagrams_dir.is_dir():
        return []
    return sorted(diagrams_dir.rglob("*.c4"), key=lambda p: str(p))


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


def is_praxion_project(root: Path) -> bool:
    """Return True iff at least one of ``.ai-state/`` or ``.ai-work/`` exists at root.

    Raises FileNotFoundError if *root* itself does not exist.
    """
    _require_root(root)
    return (root / ".ai-state").is_dir() or (root / ".ai-work").is_dir()
