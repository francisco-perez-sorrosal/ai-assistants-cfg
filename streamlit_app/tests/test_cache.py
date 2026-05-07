"""
Behavioral tests for streamlit_app/data/cache.py.

The cache module is the ONLY data-layer module permitted to import streamlit.
It wraps filesystem + parsing functions with @st.cache_data using mtime-keyed
(parser wrappers) or TTL-based (discovery wrappers) invalidation.

REGISTERED OBJECTION (API contract mismatch between IMPLEMENTATION_PLAN and task)
----------------------------------------------------------------------------------
An earlier draft of the plan described a simpler lower-level API:
  get_mtime(path) -> float, cached_read_file, cached_read_json, cached_list_dir.

The pair contract specifies a higher-level API wrapping parsers and
discovery: mtime_of, cached_parse_*, cached_list_*, clear_all.

The implementer shipped the task-prompt API (richer, parser-wrapping layer).
These tests target the shipped implementation.  The IMPLEMENTATION_PLAN API
(lower-level read primitives) was never implemented.  Flag for planner to update
the plan to match the actual design.

Concurrent-mode GREEN handshake
---------------------------------
Implementer (5a) raced ahead and shipped the full module before these tests were
written.  All tests pass immediately.  This matches the documented pattern from
Steps 3b and 4b.  The behavioral contract is verified by checking the task-prompt
API, not the stub from the plan.

Deferred imports
-----------------
`from streamlit_app.data import cache` is inside each test body (not at module
top) so pytest collection succeeds even if the module is unavailable.

Cache isolation
---------------
`_clear_caches` (autouse) calls `cache.clear_all()` before and after each test
to prevent inter-test cache contamination.  Uses try/except so the fixture works
during collection before the module exists.
"""

from __future__ import annotations

import ast
import inspect
import time
from pathlib import Path
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed(root: Path, structure: dict[str, Any]) -> None:
    """Recursively create files and directories from a nested dict.

    Keys are path components (relative to *root*).  A value of None creates
    an empty file; a str value writes that content; a dict value creates a
    directory and recurses.
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
# Cache-isolation fixture
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_caches() -> Any:
    """Clear all @st.cache_data caches before and after each test.

    Uses clear_all() if the module is importable.  Defensive against
    ImportError during concurrent-mode pre-implementation collection.
    """
    try:
        from streamlit_app.data import cache as _mod

        _mod.clear_all()
    except Exception:
        pass

    yield

    try:
        from streamlit_app.data import cache as _mod

        _mod.clear_all()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Group 1 — mtime_of
# ---------------------------------------------------------------------------


class TestMtimeOf:
    def test_returns_mtime_for_existing_file(self, tmp_path: Path) -> None:
        """mtime_of returns a positive float equal to the file's stat mtime."""
        from streamlit_app.data import cache

        f = tmp_path / "existing.md"
        f.write_text("content", encoding="utf-8")

        result = cache.mtime_of(f)

        assert isinstance(result, float)
        assert result > 0.0
        assert result == f.stat().st_mtime

    def test_returns_zero_for_missing_file(self, tmp_path: Path) -> None:
        """mtime_of returns 0.0 when the path does not exist — stable cache key."""
        from streamlit_app.data import cache

        absent = tmp_path / "does-not-exist.md"

        result = cache.mtime_of(absent)

        assert result == 0.0

    def test_returns_mtime_for_existing_directory(self, tmp_path: Path) -> None:
        """mtime_of works on directories, not only files."""
        from streamlit_app.data import cache

        d = tmp_path / "subdir"
        d.mkdir()

        result = cache.mtime_of(d)

        assert isinstance(result, float)
        assert result > 0.0

    def test_does_not_raise_on_deeply_absent_path(self, tmp_path: Path) -> None:
        """mtime_of must not raise for any non-existent path."""
        from streamlit_app.data import cache

        absent = tmp_path / "no" / "such" / "path.md"

        result = cache.mtime_of(absent)

        assert result == 0.0


# ---------------------------------------------------------------------------
# Group 2 — cached_parse_frontmatter (representative parser wrapper)
# ---------------------------------------------------------------------------


class TestCachedParseFrontmatter:
    def test_returns_frontmatter_and_body_for_valid_file(self, tmp_path: Path) -> None:
        """cached_parse_frontmatter returns (meta_dict, body_str) for a file
        with valid YAML frontmatter."""
        from streamlit_app.data import cache

        f = tmp_path / "adr.md"
        f.write_text("---\nfoo: bar\n---\nbody text\n", encoding="utf-8")
        mtime = cache.mtime_of(f)

        meta, body = cache.cached_parse_frontmatter(str(f), mtime)

        assert meta == {"foo": "bar"}
        assert "body text" in body

    def test_cache_hit_on_same_mtime(self, tmp_path: Path) -> None:
        """Two calls with identical _mtime and path return the same cached value."""
        from streamlit_app.data import cache

        f = tmp_path / "doc.md"
        f.write_text("---\ntitle: Test\n---\nbody\n", encoding="utf-8")
        mtime = cache.mtime_of(f)

        first = cache.cached_parse_frontmatter(str(f), mtime)
        second = cache.cached_parse_frontmatter(str(f), mtime)

        assert first == second

    def test_cache_refreshes_after_clear_all(self, tmp_path: Path) -> None:
        """After clear_all(), the next call re-reads the updated file content.

        NOTE on Streamlit's _mtime convention: parameters prefixed with _ are
        EXCLUDED from Streamlit's cache key hash.  Changing _mtime alone does NOT
        cause a cache miss — it is a signal by convention only.  The actual
        invalidation mechanism is clear_all() (or per-function .clear()).
        This test verifies that behavioral contract: update file → clear_all()
        → next call returns updated content.
        """
        from streamlit_app.data import cache

        f = tmp_path / "evolving.md"
        f.write_text("---\nversion: 1\n---\nbody-v1\n", encoding="utf-8")
        mtime = cache.mtime_of(f)
        meta1, body1 = cache.cached_parse_frontmatter(str(f), mtime)
        assert meta1.get("version") == 1

        # Update the file
        f.write_text("---\nversion: 2\n---\nbody-v2\n", encoding="utf-8")

        # Without clearing, the cache serves the old value (same path_str key)
        meta_stale, _ = cache.cached_parse_frontmatter(str(f), mtime)
        assert meta_stale.get("version") == 1, (
            "Expected stale cached value before clear_all(); "
            "this confirms _mtime does NOT bust the cache on its own"
        )

        # After clear_all(), the next call re-reads the updated content
        cache.clear_all()
        mtime2 = cache.mtime_of(f)
        meta2, body2 = cache.cached_parse_frontmatter(str(f), mtime2)
        assert meta2.get("version") == 2
        assert body2 != body1


# ---------------------------------------------------------------------------
# Group 3 — cached_parse_metrics_log (DataFrame-returning wrapper)
# ---------------------------------------------------------------------------

_METRICS_LOG_ROWS = """\
| timestamp | report_file |
| --- | --- |
| 2026-01-01T00:00:00Z | METRICS_REPORT_2026-01-01.md |
| 2026-01-02T00:00:00Z | METRICS_REPORT_2026-01-02.md |
"""


class TestCachedParseMetricsLog:
    def test_returns_dataframe_for_valid_log(self, tmp_path: Path) -> None:
        """cached_parse_metrics_log returns a non-empty DataFrame from a valid log."""
        import pandas as pd

        from streamlit_app.data import cache

        f = tmp_path / "METRICS_LOG.md"
        f.write_text(_METRICS_LOG_ROWS, encoding="utf-8")
        mtime = cache.mtime_of(f)

        df = cache.cached_parse_metrics_log(str(f), mtime)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "timestamp" in df.columns

    def test_returns_empty_dataframe_for_missing_file(self, tmp_path: Path) -> None:
        """cached_parse_metrics_log returns an empty DataFrame for a missing file."""
        import pandas as pd

        from streamlit_app.data import cache

        absent = tmp_path / "METRICS_LOG.md"
        mtime = cache.mtime_of(absent)  # 0.0

        df = cache.cached_parse_metrics_log(str(absent), mtime)

        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_cache_hit_on_same_mtime(self, tmp_path: Path) -> None:
        """Two calls with the same _mtime return identical DataFrames."""
        from streamlit_app.data import cache

        f = tmp_path / "METRICS_LOG.md"
        f.write_text(_METRICS_LOG_ROWS, encoding="utf-8")
        mtime = cache.mtime_of(f)

        first = cache.cached_parse_metrics_log(str(f), mtime)
        second = cache.cached_parse_metrics_log(str(f), mtime)

        # DataFrames have identical shape and column names
        assert list(first.columns) == list(second.columns)
        assert len(first) == len(second)


# ---------------------------------------------------------------------------
# Group 4 — cached_list_active_workshops (TTL-based discovery wrapper)
# ---------------------------------------------------------------------------


class TestCachedListActiveWorkshops:
    def test_returns_list_of_strings_not_paths(self, tmp_path: Path) -> None:
        """cached_list_active_workshops returns str paths, not Path objects.

        @st.cache_data requires hashable return values; str satisfies this
        even when the callers ultimately convert back to Path.
        """
        from streamlit_app.data import cache

        _seed(
            tmp_path,
            {
                ".ai-work": {
                    "feature-a": {"WIP.md": "# wip"},
                    "feature-b": {"WIP.md": "# wip"},
                }
            },
        )
        bucket = int(time.time() / 15)

        result = cache.cached_list_active_workshops(str(tmp_path), bucket)

        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, str), (
                f"Expected str paths but got {type(item).__name__}: {item!r}"
            )

    def test_returns_paths_under_ai_work(self, tmp_path: Path) -> None:
        """Each returned string represents an .ai-work/<slug>/ directory path."""
        from streamlit_app.data import cache

        _seed(
            tmp_path,
            {
                ".ai-work": {
                    "pipeline-a": {"WIP.md": "# a"},
                }
            },
        )
        bucket = int(time.time() / 15)

        result = cache.cached_list_active_workshops(str(tmp_path), bucket)

        assert any("pipeline-a" in p for p in result), (
            f"Expected 'pipeline-a' slug in results, got: {result}"
        )

    def test_same_bucket_returns_cached_value(self, tmp_path: Path) -> None:
        """Two calls with the same _now_bucket return the same result (cache hit)."""
        from streamlit_app.data import cache

        _seed(tmp_path, {".ai-work": {"slug-x": {"WIP.md": "# x"}}})
        bucket = int(time.time() / 15)

        first = cache.cached_list_active_workshops(str(tmp_path), bucket)
        second = cache.cached_list_active_workshops(str(tmp_path), bucket)

        assert first == second

    def test_empty_when_no_ai_work_directory(self, tmp_path: Path) -> None:
        """Returns [] when .ai-work/ does not exist (no raise)."""
        from streamlit_app.data import cache

        # Only .ai-state/ present; no .ai-work/
        _seed(tmp_path, {".ai-state": {}})
        bucket = int(time.time() / 15)

        result = cache.cached_list_active_workshops(str(tmp_path), bucket)

        assert result == []


class TestCachedListAdrsFinalizedAndDrafts:
    def test_finalized_paths_returned_as_strings(self, tmp_path: Path) -> None:
        """cached_list_adrs_finalized returns str paths for finalized ADR files."""
        from streamlit_app.data import cache

        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "decisions": {
                        "001-first.md": "---\nid: dec-001\n---",
                        "002-second.md": "---\nid: dec-002\n---",
                        "drafts": {},
                    }
                }
            },
        )
        bucket = int(time.time() / 15)

        result = cache.cached_list_adrs_finalized(str(tmp_path), bucket)

        assert isinstance(result, list)
        assert len(result) == 2
        for item in result:
            assert isinstance(item, str)

    def test_drafts_excluded_from_finalized_list(self, tmp_path: Path) -> None:
        """cached_list_adrs_finalized must not include any draft ADR paths."""
        from streamlit_app.data import cache

        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "decisions": {
                        "001-finalized.md": "---\nid: dec-001\n---",
                        "drafts": {
                            "20260507-1900-user-branch-draft.md": "---\nid: dec-draft-abc\n---",
                        },
                    }
                }
            },
        )
        bucket = int(time.time() / 15)

        result = cache.cached_list_adrs_finalized(str(tmp_path), bucket)

        # Check that no returned path has "drafts" as a directory component —
        # use Path.parts to avoid false matches from pytest's tmp_path prefix
        # (tmp_path may contain the test function name which includes "draft").
        draft_paths = [p for p in result if "drafts" in Path(p).parts]
        assert draft_paths == [], (
            f"Draft-directory paths found in finalized list: {draft_paths}"
        )

    def test_drafts_list_returns_draft_paths(self, tmp_path: Path) -> None:
        """cached_list_adrs_drafts returns str paths from decisions/drafts/."""
        from streamlit_app.data import cache

        _seed(
            tmp_path,
            {
                ".ai-state": {
                    "decisions": {
                        "001-finalized.md": "---\nid: dec-001\n---",
                        "drafts": {
                            "20260507-1900-user-branch-slug.md": "---\nid: dec-draft-xyz\n---",
                        },
                    }
                }
            },
        )
        bucket = int(time.time() / 15)

        result = cache.cached_list_adrs_drafts(str(tmp_path), bucket)

        assert isinstance(result, list)
        assert any("drafts" in p for p in result)
        assert not any("001-finalized" in p for p in result)


# ---------------------------------------------------------------------------
# Group 5 — clear_all
# ---------------------------------------------------------------------------


class TestClearAll:
    def test_clear_all_callable_without_error(self) -> None:
        """clear_all() must complete without raising any exception."""
        from streamlit_app.data import cache

        # Pre-populate by calling a cached function
        cache.cached_parse_wip(str(Path("/nonexistent/WIP.md")), 0.0)

        # Must not raise
        cache.clear_all()

    def test_clear_all_is_idempotent(self) -> None:
        """Calling clear_all() twice in a row must not raise."""
        from streamlit_app.data import cache

        cache.clear_all()
        cache.clear_all()


# ---------------------------------------------------------------------------
# Group 6 — Convention checks
# ---------------------------------------------------------------------------


class TestCacheModuleConventions:
    def test_cache_module_imports_only_cache_data_from_streamlit(self) -> None:
        """cache.py may import only `cache_data` from `streamlit`.

        Convention 1 explicitly allows st.cache_data in the cache module and
        forbids all rendering primitives (st.write, st.markdown, etc.).

        Verified via AST parse — does not require executing the module.
        """
        cache_path = Path(__file__).parent.parent / "data" / "cache.py"
        assert cache_path.exists(), (
            f"cache.py not found at {cache_path}; "
            "cannot verify Convention 1 without source file"
        )
        source = cache_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(cache_path))

        forbidden: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    if name == "streamlit" or name.startswith("streamlit."):
                        # bare `import streamlit` is forbidden; only allowed form
                        # is `from streamlit import cache_data`
                        forbidden.append(f"import {name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module == "streamlit" or module.startswith("streamlit."):
                    for alias in node.names:
                        if alias.name != "cache_data":
                            forbidden.append(f"from {module} import {alias.name}")

        assert forbidden == [], (
            "cache.py imports Streamlit symbols other than cache_data "
            f"(Convention 1 violation): {forbidden}"
        )

    def test_every_cached_parse_function_takes_mtime_arg(self) -> None:
        """Every cached_parse_* function declares an `mtime: float` parameter.

        Convention 2: cache_data parser wrappers MUST take `mtime` (no leading
        underscore) so the value participates in the cache hash. A leading
        underscore tells Streamlit to EXCLUDE the parameter from the hash —
        which silently breaks invalidation. See memory
        `streamlit-cache-data-underscore-prefix-excludes-from-hash`.

        Verified via inspect so decorator wrapping does not hide parameters.
        """
        from streamlit_app.data import cache as cache_mod

        missing_mtime: list[str] = []
        for name in dir(cache_mod):
            if not name.startswith("cached_parse_"):
                continue
            fn = getattr(cache_mod, name)
            if not callable(fn):
                continue
            try:
                sig = inspect.signature(fn)
                params = sig.parameters
            except (ValueError, TypeError):
                continue

            if "mtime" not in params:
                missing_mtime.append(name)

        assert missing_mtime == [], (
            "The following cached_parse_* functions are missing `mtime` "
            f"(Convention 2 violation): {missing_mtime}"
        )

    def test_cached_parse_functions_use_mtime_without_underscore(self) -> None:
        """Every cached_parse_* function's second positional parameter is `mtime`
        (NOT `_mtime`).

        The leading underscore tells Streamlit's `@st.cache_data` to EXCLUDE the
        parameter from the cache-key hash — which silently breaks invalidation
        (cache hits return stale data forever, until ttl expires or clear_all()
        is called). For mtime to actually invalidate the cache, the parameter
        must be hashable in the key — i.e., NOT underscore-prefixed.

        See memory `streamlit-cache-data-underscore-prefix-excludes-from-hash`.

        Uses AST inspection because @cache_data wraps the decorated function and
        hides original parameter names from inspect.signature.
        """
        cache_path = Path(__file__).parent.parent / "data" / "cache.py"
        assert cache_path.exists(), (
            "cache.py not found; cannot verify parameter convention"
        )

        source = cache_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(cache_path))

        violations: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            # Only check parser wrappers — list wrappers use TTL+bucket (different pattern).
            if not node.name.startswith("cached_parse_"):
                continue

            params = [a.arg for a in node.args.args]
            if len(params) < 2:
                violations.append(f"{node.name}: fewer than 2 positional params")
                continue

            second_param = params[1]
            if second_param != "mtime":
                violations.append(
                    f"{node.name}: second param '{second_param}' must be `mtime` "
                    "(no underscore — see Convention 2; underscore EXCLUDES from hash)"
                )

        assert violations == [], (
            "Convention 2 violation — cached_parse_* second param must be `mtime` "
            f"(no underscore): {violations}"
        )
