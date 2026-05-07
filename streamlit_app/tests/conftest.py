"""
Pytest fixtures for the Praxion Pipeline Dashboard test suite.

Fixtures (added as test modules are created)
---------------------------------------
  project_root(tmp_path)
      A minimal Praxion-onboarded project tree built under tmp_path:
          <root>/
            .ai-state/
              decisions/
                drafts/
              sentinel_reports/
              metrics_reports/
              ARCHITECTURE.md
            .ai-work/
              sample-pipeline/
                WIP.md
                PROGRESS.md
            ROADMAP.md

  empty_project_root(tmp_path)
      A project tree with .ai-state/ and .ai-work/ present but empty.
      Used to verify graceful degradation across all pages.

  monkeypatch_project_root(monkeypatch, project_root)
      Set PRAXION_PROJECT_ROOT env var to the fixture project root,
      so modules that call os.environ["PRAXION_PROJECT_ROOT"] work in tests.

Notes
-----
  - All fixtures use tmp_path (function-scoped) to ensure isolation.
  - Do NOT use module-scoped fixtures combined with autouse reset fixtures
    (causes KeyError on second test — see memory: pytest fixture scoping gotcha).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest


def _seed(root: Path, structure: dict[str, Any]) -> None:
    """Recursively create files and directories from a nested dict.

    Keys are path components (relative to *root*).  A value of None creates
    an empty file; a str value writes that content; a dict value creates a
    directory and recurses.

    This utility is also available directly in test modules that import it
    locally.  Kept here for fixtures that need it.
    """
    for name, value in structure.items():
        target = root / name
        if isinstance(value, dict):
            target.mkdir(parents=True, exist_ok=True)
            _seed(target, value)
        elif value is None:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.touch()
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(value), encoding="utf-8")


@pytest.fixture()
def project_root(tmp_path: Path) -> Path:
    """Minimal Praxion-onboarded project tree.

    Contains representative files for each artifact type so page modules
    can exercise their happy paths without building the tree from scratch.
    Returns the root path.
    """
    _seed(
        tmp_path,
        {
            ".ai-state": {
                "ARCHITECTURE.md": "# Architecture\n\n## Components\n",
                "SYSTEM_DEPLOYMENT.md": "# Deployment\n",
                "TEST_TOPOLOGY.md": "# Test Topology\n",
                "calibration_log.md": "# Calibration Log\n",
                "TECH_DEBT_LEDGER.md": "# Tech Debt\n",
                "TECH_DEBT_RESOLVED.md": "# Resolved\n",
                "decisions": {
                    "DECISIONS_INDEX.md": "# Index\n",
                    "001-first-decision.md": "---\nid: dec-001\ntitle: First\n---\n",
                    "drafts": {
                        "20260507-1900-user-branch-draft.md": "---\nid: dec-draft-abc\n---\n",
                    },
                },
                "sentinel_reports": {
                    "SENTINEL_LOG.md": "# Sentinel Log\n",
                    "SENTINEL_REPORT_2026-01-01_00-00-00.md": "# Report\n",
                },
                "metrics_reports": {
                    "METRICS_LOG.md": "# Metrics Log\n",
                    "METRICS_REPORT_2026-01-01.md": "# MD Report\n",
                    "METRICS_REPORT_2026-01-01.json": '{"schema_version":"1.0.0"}',
                },
                "idea_ledgers": {
                    "IDEA_LEDGER_2026-01-01_00-00-00.md": "# Ideas\n",
                },
                "specs": {
                    "SPEC_sample_2026-01-01.md": "# Spec\n",
                },
            },
            ".ai-work": {
                "sample-pipeline": {
                    "WIP.md": "# WIP\n",
                    "PROGRESS.md": "# Progress\n",
                    "SYSTEMS_PLAN.md": "# Systems Plan\n",
                    "IMPLEMENTATION_PLAN.md": "# Impl Plan\n",
                    "LEARNINGS.md": "# Learnings\n",
                },
            },
            "ROADMAP.md": "# Roadmap\n",
            "docs": {
                "architecture.md": "# Dev Architecture Guide\n",
                "diagrams": {
                    "architecture.c4": "specification context { }",
                    "architecture": {
                        "context.svg": "<svg/>",
                        "components.svg": "<svg/>",
                    },
                },
            },
        },
    )
    return tmp_path


@pytest.fixture()
def empty_project_root(tmp_path: Path) -> Path:
    """Project tree with .ai-state/ and .ai-work/ present but empty.

    Used to verify graceful degradation: every discovery function must return
    None or [] rather than raising an exception.
    """
    _seed(
        tmp_path,
        {
            ".ai-state": {
                "decisions": {
                    "drafts": {},
                },
                "sentinel_reports": {},
                "metrics_reports": {},
                "idea_ledgers": {},
                "specs": {},
            },
            ".ai-work": {},
        },
    )
    return tmp_path


@pytest.fixture()
def monkeypatch_project_root(
    monkeypatch: pytest.MonkeyPatch, project_root: Path
) -> Path:
    """Set PRAXION_PROJECT_ROOT to the fixture project root.

    Modules that read os.environ["PRAXION_PROJECT_ROOT"] at call time (not at
    import time) will see the tmp_path root.  Returns the root path for
    convenience.
    """
    monkeypatch.setenv("PRAXION_PROJECT_ROOT", str(project_root))
    return project_root
