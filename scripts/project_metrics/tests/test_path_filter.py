"""Behavioral tests for the shared path-filter module.

The filter is consumed by three collectors (``git``, ``scc``, ``lizard``)
to keep ecosystem-noise directories (``.ai-state``, ``.ai-work``, build
caches, virtualenvs) from polluting per-file metrics. Tests exercise the
predicate, the dict helper, and both tool-specific argv emitters
independently so a regression in any one surface is localized.
"""

from __future__ import annotations

import pytest

from scripts.project_metrics._path_filter import (
    DEFAULT_EXCLUDED_DIRS,
    filter_path_dict,
    is_excluded_path,
    lizard_exclude_args,
    scc_exclude_dir_args,
)


class TestIsExcludedPath:
    """Component-boundary semantics for the predicate."""

    @pytest.mark.parametrize(
        "path",
        [
            ".ai-state/ARCHITECTURE.md",
            ".ai-state/decisions/000-foo.md",
            "foo/.ai-state/bar",
            ".ai-work/task/SYSTEMS_PLAN.md",
            ".claude/worktrees/scratch/file.py",
            ".cursor/rules/foo.md",
            "node_modules/foo/index.js",
            "foo/__pycache__/bar.pyc",
            ".git/HEAD",
            ".venv/lib/python3.11/site-packages/foo.py",
            "./.ai-state/foo.md",
        ],
    )
    def test_returns_true_for_paths_under_excluded_dirs(self, path: str) -> None:
        assert is_excluded_path(path) is True

    @pytest.mark.parametrize(
        "path",
        [
            "src/main.py",
            "scripts/project_metrics/cli.py",
            "README.md",
            "docs/architecture.md",
            "test_foo.py",
            ".claude/agents/sentinel.md",
            ".ai-state-but-not-really.md",
            "ai-state/foo.md",
            "./scripts/foo.py",
        ],
    )
    def test_returns_false_for_real_project_paths(self, path: str) -> None:
        assert is_excluded_path(path) is False

    def test_empty_path_returns_false(self) -> None:
        assert is_excluded_path("") is False

    def test_custom_exclusion_set_overrides_default(self) -> None:
        custom = frozenset({"foo"})
        assert is_excluded_path("foo/bar.py", excluded=custom) is True
        assert is_excluded_path(".ai-state/x.md", excluded=custom) is False

    def test_multi_component_exclusion_requires_contiguous_match(self) -> None:
        assert is_excluded_path(".claude/worktrees/x") is True
        assert is_excluded_path(".claude/agents/x") is False
        assert is_excluded_path("worktrees/x") is False


class TestFilterPathDict:
    """``filter_path_dict`` is shape-preserving and non-mutating."""

    def test_drops_excluded_keys_only(self) -> None:
        original = {
            ".ai-state/foo": 1,
            "src/main.py": 2,
            ".claude/worktrees/x": 3,
            "README.md": 4,
        }
        filtered = filter_path_dict(original)
        assert filtered == {"src/main.py": 2, "README.md": 4}

    def test_does_not_mutate_input(self) -> None:
        original = {".ai-state/foo": 1, "src/main.py": 2}
        snapshot = dict(original)
        filter_path_dict(original)
        assert original == snapshot

    def test_preserves_insertion_order(self) -> None:
        original = {"a/x": 1, ".ai-state/y": 2, "b/z": 3}
        filtered = filter_path_dict(original)
        assert list(filtered.keys()) == ["a/x", "b/z"]

    def test_empty_input_returns_empty_dict(self) -> None:
        assert filter_path_dict({}) == {}


class TestSccExcludeDirArgs:
    """``--exclude-dir <csv>`` flag generation for scc."""

    def test_returns_two_argv_tokens_with_csv_payload(self) -> None:
        argv = scc_exclude_dir_args()
        assert len(argv) == 2
        assert argv[0] == "--exclude-dir"
        # CSV is alphabetically sorted for determinism
        assert argv[1].split(",") == sorted(argv[1].split(","))

    def test_csv_excludes_multi_component_entries(self) -> None:
        argv = scc_exclude_dir_args()
        csv = argv[1]
        # .claude/worktrees is multi-component; cannot be expressed via --exclude-dir
        assert ".claude/worktrees" not in csv
        # Single-component entries are present
        assert ".ai-state" in csv.split(",")
        assert ".ai-work" in csv.split(",")
        assert "node_modules" in csv.split(",")

    def test_returns_empty_list_when_no_single_component_entries(self) -> None:
        custom = frozenset({"a/b"})  # only a multi-component entry
        assert scc_exclude_dir_args(excluded=custom) == []


class TestLizardExcludeArgs:
    """``--exclude PATTERN`` repeated-flag generation for lizard."""

    def test_emits_one_flag_per_excluded_entry(self) -> None:
        argv = lizard_exclude_args()
        flags = [token for token in argv if token == "--exclude"]
        assert len(flags) == len(DEFAULT_EXCLUDED_DIRS)

    def test_uses_glob_pattern_shape(self) -> None:
        argv = lizard_exclude_args()
        for index, token in enumerate(argv):
            if token == "--exclude":
                pattern = argv[index + 1]
                assert pattern.startswith("*/")
                assert pattern.endswith("/*")

    def test_multi_component_entry_keeps_internal_slashes(self) -> None:
        argv = lizard_exclude_args()
        assert "*/.claude/worktrees/*" in argv

    def test_custom_excluded_set(self) -> None:
        custom = frozenset({"x", "y/z"})
        argv = lizard_exclude_args(excluded=custom)
        assert argv == ["--exclude", "*/x/*", "--exclude", "*/y/z/*"]
