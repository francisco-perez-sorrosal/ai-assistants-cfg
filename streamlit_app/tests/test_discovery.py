"""
Behavioral tests for streamlit_app/data/discovery.py.

All functions are pure — they locate files relative to a given root and
return Optional[Path] (singletons) or list[Path] (collections).  Tests use
tmp_path to build minimal fake project trees; no mocks are needed.

Imports of the module under test are deferred to each test body so that
pytest collection succeeds even before the implementation exists (concurrent
BDD/TDD RED handshake protocol).
"""

from __future__ import annotations

import ast
import time
from pathlib import Path
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _seed(root: Path, structure: dict[str, Any]) -> None:
    """Recursively create files and directories from a nested dict.

    Keys are path components (relative to *root*).  A value of None creates
    an empty file; a str value writes that content; a dict value creates a
    directory and recurses.

    Example::
        _seed(tmp_path, {
            ".ai-state": {
                "ARCHITECTURE.md": "# arch",
                "decisions": {"001-a.md": "---\\nid: dec-001\\n---"},
            },
            "ROADMAP.md": None,
        })
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


# ---------------------------------------------------------------------------
# Group 1 — Sparse / empty projects (graceful degradation)
# ---------------------------------------------------------------------------


class TestSparseAndEmptyProjects:
    def test_empty_project_returns_none_or_empty(self, tmp_path: Path) -> None:
        """Every discovery function returns None or [] when the project root has
        no .ai-state/ and no .ai-work/ directories."""
        from streamlit_app.data import discovery

        # All Optional[Path] singletons must return None
        assert discovery.find_architecture_md(tmp_path) is None
        assert discovery.find_system_deployment(tmp_path) is None
        assert discovery.find_test_topology(tmp_path) is None
        assert discovery.find_calibration_log(tmp_path) is None
        assert discovery.find_tech_debt_active(tmp_path) is None
        assert discovery.find_tech_debt_resolved(tmp_path) is None
        assert discovery.find_decisions_index(tmp_path) is None
        assert discovery.find_sentinel_log(tmp_path) is None
        assert discovery.find_metrics_log(tmp_path) is None
        assert discovery.find_roadmap(tmp_path) is None
        assert discovery.find_developer_architecture(tmp_path) is None

        # All list[Path] collections must return []
        assert discovery.list_adrs_finalized(tmp_path) == []
        assert discovery.list_adrs_drafts(tmp_path) == []
        assert discovery.list_sentinel_reports(tmp_path) == []
        assert discovery.list_metrics_reports_md(tmp_path) == []
        assert discovery.list_metrics_reports_json(tmp_path) == []
        assert discovery.list_idea_ledgers(tmp_path) == []
        assert discovery.list_specs(tmp_path) == []
        assert discovery.list_active_workshops(tmp_path) == []
        assert discovery.list_likec4_svgs(tmp_path) == []
        assert discovery.list_likec4_sources(tmp_path) == []

    def test_is_praxion_project_false_for_empty_dir(self, tmp_path: Path) -> None:
        """A directory with neither .ai-state/ nor .ai-work/ is not a Praxion project."""
        from streamlit_app.data import discovery

        assert discovery.is_praxion_project(tmp_path) is False

    def test_is_praxion_project_true_with_ai_state_only(self, tmp_path: Path) -> None:
        """Presence of .ai-state/ alone is sufficient to mark a project as Praxion."""
        from streamlit_app.data import discovery

        _seed(tmp_path, {".ai-state": {}})
        assert discovery.is_praxion_project(tmp_path) is True

    def test_is_praxion_project_true_with_ai_work_only(self, tmp_path: Path) -> None:
        """Presence of .ai-work/ alone is sufficient to mark a project as Praxion."""
        from streamlit_app.data import discovery

        _seed(tmp_path, {".ai-work": {"feature-a": {"WIP.md": None}}})
        assert discovery.is_praxion_project(tmp_path) is True

    def test_missing_root_raises_file_not_found(self, tmp_path: Path) -> None:
        """All discovery functions raise FileNotFoundError when root does not exist."""
        from streamlit_app.data import discovery

        absent = tmp_path / "does-not-exist"

        with pytest.raises(FileNotFoundError):
            discovery.find_architecture_md(absent)

        with pytest.raises(FileNotFoundError):
            discovery.list_adrs_finalized(absent)

        with pytest.raises(FileNotFoundError):
            discovery.list_active_workshops(absent)

        with pytest.raises(FileNotFoundError):
            discovery.is_praxion_project(absent)


# ---------------------------------------------------------------------------
# Group 2 — .ai-state/ discovery (stateful / persistent artifacts)
# ---------------------------------------------------------------------------


class TestAiStateDiscovery:
    def test_find_architecture_md_present(self, tmp_path: Path) -> None:
        """find_architecture_md returns the path when ARCHITECTURE.md exists."""
        from streamlit_app.data import discovery

        _seed(tmp_path, {".ai-state": {"ARCHITECTURE.md": "# arch"}})
        result = discovery.find_architecture_md(tmp_path)
        assert result is not None
        assert result == tmp_path / ".ai-state" / "ARCHITECTURE.md"

    def test_find_architecture_md_absent(self, tmp_path: Path) -> None:
        """find_architecture_md returns None when ARCHITECTURE.md is missing."""
        from streamlit_app.data import discovery

        _seed(tmp_path, {".ai-state": {}})
        assert discovery.find_architecture_md(tmp_path) is None

    def test_find_system_deployment_present_and_absent(self, tmp_path: Path) -> None:
        """find_system_deployment returns path when SYSTEM_DEPLOYMENT.md exists."""
        from streamlit_app.data import discovery

        _seed(tmp_path, {".ai-state": {"SYSTEM_DEPLOYMENT.md": "# deploy"}})
        result = discovery.find_system_deployment(tmp_path)
        assert result == tmp_path / ".ai-state" / "SYSTEM_DEPLOYMENT.md"

        _seed(tmp_path / "empty", {".ai-state": {}})
        assert discovery.find_system_deployment(tmp_path / "empty") is None

    def test_find_tech_debt_active_and_resolved(self, tmp_path: Path) -> None:
        """find_tech_debt_active and find_tech_debt_resolved locate their
        respective files independently."""
        from streamlit_app.data import discovery

        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "TECH_DEBT_LEDGER.md": "# active",
                    "TECH_DEBT_RESOLVED.md": "# resolved",
                }
            },
        )
        assert discovery.find_tech_debt_active(tmp_path) == (
            tmp_path / ".ai-state" / "TECH_DEBT_LEDGER.md"
        )
        assert discovery.find_tech_debt_resolved(tmp_path) == (
            tmp_path / ".ai-state" / "TECH_DEBT_RESOLVED.md"
        )

    def test_list_adrs_finalized_filename_pattern(self, tmp_path: Path) -> None:
        """list_adrs_finalized returns only files matching NNN-slug.md and sorts
        them by the leading numeric prefix ascending."""
        from streamlit_app.data import discovery

        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "decisions": {
                        "001-authentication.md": "# adr 1",
                        "002-caching.md": "# adr 2",
                        "not-an-adr.md": "# not finalized",
                        "README.md": "# index",
                        "drafts": {},
                    }
                }
            },
        )
        result = discovery.list_adrs_finalized(tmp_path)
        assert len(result) == 2
        # Sorted ascending by NNN
        assert result[0].name == "001-authentication.md"
        assert result[1].name == "002-caching.md"

    def test_list_adrs_finalized_excludes_drafts(self, tmp_path: Path) -> None:
        """Finalized ADR list must not include any file under decisions/drafts/."""
        from streamlit_app.data import discovery

        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "decisions": {
                        "001-first.md": "# finalized",
                        "drafts": {
                            "20260507-1900-user-branch-some-decision.md": "# draft",
                        },
                    }
                }
            },
        )
        finalized = discovery.list_adrs_finalized(tmp_path)
        names = [p.name for p in finalized]
        assert "001-first.md" in names
        assert not any("drafts" in str(p) for p in finalized)

    def test_list_adrs_drafts_pattern(self, tmp_path: Path) -> None:
        """list_adrs_drafts returns only files under decisions/drafts/; finalized
        files in decisions/ are excluded."""
        from streamlit_app.data import discovery

        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "decisions": {
                        "001-finalized.md": "# finalized",
                        "drafts": {
                            "20260507-1900-user-branch-slug-a.md": "# draft a",
                            "20260507-2000-user-branch-slug-b.md": "# draft b",
                        },
                    }
                }
            },
        )
        drafts = discovery.list_adrs_drafts(tmp_path)
        names = [p.name for p in drafts]
        assert "20260507-1900-user-branch-slug-a.md" in names
        assert "20260507-2000-user-branch-slug-b.md" in names
        assert "001-finalized.md" not in names

    def test_list_sentinel_reports_newest_first(self, tmp_path: Path) -> None:
        """list_sentinel_reports returns SENTINEL_REPORT_*.md files sorted
        newest (lexicographically last timestamp) first."""
        from streamlit_app.data import discovery

        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "sentinel_reports": {
                        "SENTINEL_REPORT_2026-01-01_00-00-00.md": "# old",
                        "SENTINEL_REPORT_2026-01-02_00-00-00.md": "# mid",
                        "SENTINEL_REPORT_2026-01-03_00-00-00.md": "# new",
                    }
                }
            },
        )
        reports = discovery.list_sentinel_reports(tmp_path)
        assert len(reports) == 3
        assert reports[0].name == "SENTINEL_REPORT_2026-01-03_00-00-00.md"
        assert reports[1].name == "SENTINEL_REPORT_2026-01-02_00-00-00.md"
        assert reports[2].name == "SENTINEL_REPORT_2026-01-01_00-00-00.md"

    def test_find_sentinel_log_present(self, tmp_path: Path) -> None:
        """find_sentinel_log returns the SENTINEL_LOG.md path when present."""
        from streamlit_app.data import discovery

        _seed(
            tmp_path, {".ai-state": {"sentinel_reports": {"SENTINEL_LOG.md": "# log"}}}
        )
        result = discovery.find_sentinel_log(tmp_path)
        assert result == tmp_path / ".ai-state" / "sentinel_reports" / "SENTINEL_LOG.md"

    def test_list_metrics_reports_md_and_json_separate(self, tmp_path: Path) -> None:
        """list_metrics_reports_md returns only .md files; list_metrics_reports_json
        returns only .json files — they never overlap."""
        from streamlit_app.data import discovery

        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "metrics_reports": {
                        "METRICS_REPORT_2026-01-01.md": "# md report",
                        "METRICS_REPORT_2026-01-01.json": '{"schema_version":"1.0.0"}',
                        "METRICS_REPORT_2026-01-02.md": "# md report 2",
                        "METRICS_LOG.md": "# log",
                    }
                }
            },
        )
        md_reports = discovery.list_metrics_reports_md(tmp_path)
        json_reports = discovery.list_metrics_reports_json(tmp_path)

        md_names = {p.name for p in md_reports}
        json_names = {p.name for p in json_reports}

        assert "METRICS_REPORT_2026-01-01.md" in md_names
        assert "METRICS_REPORT_2026-01-02.md" in md_names
        assert "METRICS_LOG.md" not in md_names  # log is not a report
        assert "METRICS_REPORT_2026-01-01.json" in json_names
        assert not (md_names & json_names)  # no overlap

    def test_list_idea_ledgers_newest_first(self, tmp_path: Path) -> None:
        """list_idea_ledgers returns IDEA_LEDGER_*.md files newest-first."""
        from streamlit_app.data import discovery

        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "idea_ledgers": {
                        "IDEA_LEDGER_2026-01-01_00-00-00.md": "# old",
                        "IDEA_LEDGER_2026-02-01_00-00-00.md": "# new",
                    }
                }
            },
        )
        ledgers = discovery.list_idea_ledgers(tmp_path)
        assert len(ledgers) == 2
        assert ledgers[0].name == "IDEA_LEDGER_2026-02-01_00-00-00.md"
        assert ledgers[1].name == "IDEA_LEDGER_2026-01-01_00-00-00.md"

    def test_list_specs_newest_first(self, tmp_path: Path) -> None:
        """list_specs returns SPEC_*.md files newest-first."""
        from streamlit_app.data import discovery

        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "specs": {
                        "SPEC_auth_2026-01-01.md": "# old spec",
                        "SPEC_payments_2026-03-01.md": "# new spec",
                    }
                }
            },
        )
        specs = discovery.list_specs(tmp_path)
        assert len(specs) == 2
        assert specs[0].name == "SPEC_payments_2026-03-01.md"
        assert specs[1].name == "SPEC_auth_2026-01-01.md"

    def test_find_decisions_index_present(self, tmp_path: Path) -> None:
        """find_decisions_index returns the DECISIONS_INDEX.md path when present."""
        from streamlit_app.data import discovery

        _seed(tmp_path, {".ai-state": {"decisions": {"DECISIONS_INDEX.md": "# index"}}})
        result = discovery.find_decisions_index(tmp_path)
        assert result == tmp_path / ".ai-state" / "decisions" / "DECISIONS_INDEX.md"

    def test_find_calibration_log_present(self, tmp_path: Path) -> None:
        """find_calibration_log returns the calibration_log.md path when present."""
        from streamlit_app.data import discovery

        _seed(tmp_path, {".ai-state": {"calibration_log.md": "# log"}})
        result = discovery.find_calibration_log(tmp_path)
        assert result == tmp_path / ".ai-state" / "calibration_log.md"

    def test_find_test_topology_present(self, tmp_path: Path) -> None:
        """find_test_topology returns the TEST_TOPOLOGY.md path when present."""
        from streamlit_app.data import discovery

        _seed(tmp_path, {".ai-state": {"TEST_TOPOLOGY.md": "# topology"}})
        result = discovery.find_test_topology(tmp_path)
        assert result == tmp_path / ".ai-state" / "TEST_TOPOLOGY.md"


# ---------------------------------------------------------------------------
# Group 3 — .ai-work/ discovery (ephemeral / workshops)
# ---------------------------------------------------------------------------


class TestWorkshopDiscovery:
    def test_list_active_workshops_finds_task_slug_dirs(self, tmp_path: Path) -> None:
        """list_active_workshops returns .ai-work/<slug>/ directories sorted
        by mtime newest first."""
        from streamlit_app.data import discovery

        _seed(
            tmp_path,
            {
                ".ai-work": {
                    "feature-a": {"WIP.md": None},
                    "feature-b": {"WIP.md": None},
                }
            },
        )
        # Touch feature-b so it has a later mtime than feature-a
        time.sleep(0.02)
        (tmp_path / ".ai-work" / "feature-b" / "WIP.md").touch()

        workshops = discovery.list_active_workshops(tmp_path)
        names = [p.name for p in workshops]
        assert "feature-a" in names
        assert "feature-b" in names
        # feature-b is newer — must appear first
        assert names.index("feature-b") < names.index("feature-a")

    def test_list_active_workshops_empty_if_no_ai_work(self, tmp_path: Path) -> None:
        """list_active_workshops returns [] when .ai-work/ does not exist — no raise."""
        from streamlit_app.data import discovery

        # Only .ai-state/ exists; no .ai-work/
        _seed(tmp_path, {".ai-state": {}})
        assert discovery.list_active_workshops(tmp_path) == []

    def test_list_active_workshops_skips_non_directories(self, tmp_path: Path) -> None:
        """Loose files inside .ai-work/ are not returned as workshops."""
        from streamlit_app.data import discovery

        _seed(
            tmp_path,
            {
                ".ai-work": {
                    "some-file.txt": "not a workshop",
                    "real-workshop": {"WIP.md": None},
                }
            },
        )
        workshops = discovery.list_active_workshops(tmp_path)
        names = [p.name for p in workshops]
        assert "real-workshop" in names
        assert "some-file.txt" not in names

    def test_find_workshop_artifact_present(self, tmp_path: Path) -> None:
        """find_workshop_artifact returns the path when the artifact exists inside
        the workshop directory."""
        from streamlit_app.data import discovery

        workshop_dir = tmp_path / ".ai-work" / "feature-a"
        _seed(tmp_path, {".ai-work": {"feature-a": {"WIP.md": "# wip content"}}})

        result = discovery.find_workshop_artifact(workshop_dir, "WIP.md")
        assert result == workshop_dir / "WIP.md"

    def test_find_workshop_artifact_absent(self, tmp_path: Path) -> None:
        """find_workshop_artifact returns None when the artifact is missing from
        the workshop directory."""
        from streamlit_app.data import discovery

        workshop_dir = tmp_path / ".ai-work" / "feature-a"
        _seed(tmp_path, {".ai-work": {"feature-a": {"WIP.md": None}}})

        assert discovery.find_workshop_artifact(workshop_dir, "LEARNINGS.md") is None

    def test_find_workshop_artifact_all_known_names(self, tmp_path: Path) -> None:
        """All canonical artifact names are findable via find_workshop_artifact."""
        from streamlit_app.data import discovery

        canonical_artifacts = [
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
        ]
        workshop_dir = tmp_path / ".ai-work" / "slug"
        workshop_dir.mkdir(parents=True)
        for name in canonical_artifacts:
            (workshop_dir / name).touch()

        for name in canonical_artifacts:
            result = discovery.find_workshop_artifact(workshop_dir, name)
            assert result is not None, f"Expected to find {name} but got None"


# ---------------------------------------------------------------------------
# Group 4 — Project-root files
# ---------------------------------------------------------------------------


class TestProjectRootFiles:
    def test_find_roadmap_present_and_absent(self, tmp_path: Path) -> None:
        """find_roadmap returns ROADMAP.md at project root when present, None otherwise."""
        from streamlit_app.data import discovery

        absent_root = tmp_path / "no-roadmap"
        absent_root.mkdir()
        assert discovery.find_roadmap(absent_root) is None

        _seed(tmp_path, {"ROADMAP.md": "# roadmap"})
        result = discovery.find_roadmap(tmp_path)
        assert result == tmp_path / "ROADMAP.md"

    def test_find_developer_architecture_at_docs_path(self, tmp_path: Path) -> None:
        """find_developer_architecture returns docs/architecture.md when present."""
        from streamlit_app.data import discovery

        _seed(tmp_path, {"docs": {"architecture.md": "# dev arch"}})
        result = discovery.find_developer_architecture(tmp_path)
        assert result == tmp_path / "docs" / "architecture.md"

    def test_find_developer_architecture_absent(self, tmp_path: Path) -> None:
        """find_developer_architecture returns None when docs/architecture.md is absent."""
        from streamlit_app.data import discovery

        _seed(tmp_path, {"docs": {}})
        assert discovery.find_developer_architecture(tmp_path) is None

    def test_list_likec4_svgs_recursive(self, tmp_path: Path) -> None:
        """list_likec4_svgs finds all .svg files under docs/diagrams/ recursively."""
        from streamlit_app.data import discovery

        _seed(
            tmp_path,
            {
                "docs": {
                    "diagrams": {
                        "architecture": {
                            "context.svg": "<svg/>",
                            "components.svg": "<svg/>",
                        },
                        "components.svg": "<svg/>",
                        "readme.md": "# not an svg",
                    }
                }
            },
        )
        svgs = discovery.list_likec4_svgs(tmp_path)
        names = {p.name for p in svgs}
        assert names == {"context.svg", "components.svg"}
        # All paths must be under docs/diagrams/
        for svg_path in svgs:
            assert "diagrams" in svg_path.parts

    def test_list_likec4_sources_recursive(self, tmp_path: Path) -> None:
        """list_likec4_sources finds all .c4 files under docs/diagrams/ recursively."""
        from streamlit_app.data import discovery

        _seed(
            tmp_path,
            {
                "docs": {
                    "diagrams": {
                        "architecture.c4": "specification context { }",
                        "other.txt": "not a c4",
                    }
                }
            },
        )
        sources = discovery.list_likec4_sources(tmp_path)
        names = [p.name for p in sources]
        assert "architecture.c4" in names
        assert "other.txt" not in names

    def test_list_likec4_svgs_empty_when_docs_diagrams_absent(
        self, tmp_path: Path
    ) -> None:
        """list_likec4_svgs returns [] when docs/diagrams/ does not exist."""
        from streamlit_app.data import discovery

        # No docs/ directory at all
        assert discovery.list_likec4_svgs(tmp_path) == []


# ---------------------------------------------------------------------------
# Group 5 — Purity (Convention 1: no Streamlit rendering imports in data/)
# ---------------------------------------------------------------------------


class TestDiscoveryModulePurity:
    def test_discovery_module_imports_no_streamlit_rendering(self) -> None:
        """discovery.py must not import any Streamlit rendering primitive.
        The data layer is allowed st.cache_data only; discovery.py needs
        no Streamlit imports at all.

        Verified via AST parse — does not require executing the module.
        """
        discovery_path = Path(__file__).parent.parent / "data" / "discovery.py"
        assert discovery_path.exists(), (
            f"discovery.py not found at {discovery_path}; "
            "cannot verify purity without the source file"
        )
        source = discovery_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(discovery_path))

        forbidden_imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "streamlit" or alias.name.startswith("streamlit."):
                        forbidden_imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module == "streamlit" or module.startswith("streamlit."):
                    # cache_data is the one permitted exception in data/ modules
                    # (only in cache.py, not discovery.py).  Any import from
                    # streamlit in discovery.py is forbidden.
                    for alias in node.names:
                        forbidden_imports.append(f"from {module} import {alias.name}")

        assert forbidden_imports == [], (
            f"discovery.py contains forbidden Streamlit imports "
            f"(Convention 1 — pure data layer): {forbidden_imports}"
        )
