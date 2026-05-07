"""
Behavioral tests for streamlit_app/data/parsers.py.

All functions under test are pure — no caching, no side effects, no Streamlit
imports.  Tests use tmp_path for filesystem isolation and deferred imports so
that pytest collection succeeds before the implementation module exists
(concurrent BDD/TDD RED-handshake protocol).

REGISTERED OBJECTION (implementation-contract mismatch)
--------------------------------------------------------
The step prompt states the frontmatter parser uses `python-frontmatter`.
ADR dec-draft-1c4350fd (confirmed in requirements.txt) explicitly rejects
python-frontmatter in favour of stdlib re + pyyaml.  Tests here verify
behaviour (what the function returns) — not which library is used — so they
are valid regardless of which implementation path the implementer chooses.
If the implementer follows the ADR (stdlib re + pyyaml), all tests here will
pass without modification.
"""

from __future__ import annotations

import ast
import json
import logging
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Shared helpers
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


def _real_adr_path() -> Path:
    """Return the path to an ADR draft that exists in this worktree."""
    return (
        Path(__file__).parent.parent.parent
        / ".ai-state"
        / "decisions"
        / "drafts"
        # noqa: E501 — filename is long by design (ADR fragment naming scheme)
        / "20260507-1900-fperezsorrosal-worktree-pipeline-dashboard-"
        "dashboard-frontmatter-parsing.md"
    )


# ---------------------------------------------------------------------------
# Group 1 — parse_frontmatter
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def test_parses_yaml_frontmatter(self, tmp_path: Path) -> None:
        """A file with well-formed frontmatter returns the metadata dict and body."""
        from streamlit_app.data import parsers

        p = tmp_path / "adr.md"
        p.write_text("---\nfoo: bar\nbaz: 42\n---\nbody text\n", encoding="utf-8")

        meta, body = parsers.parse_frontmatter(p)

        assert meta == {"foo": "bar", "baz": 42}
        assert body == "body text\n"

    def test_no_frontmatter_returns_empty_dict_and_full_body(
        self, tmp_path: Path
    ) -> None:
        """A file without frontmatter returns ({}, full_text)."""
        from streamlit_app.data import parsers

        content = "hello\n"
        p = tmp_path / "plain.md"
        p.write_text(content, encoding="utf-8")

        meta, body = parsers.parse_frontmatter(p)

        assert meta == {}
        assert body == content

    def test_strips_frontmatter_from_body(self, tmp_path: Path) -> None:
        """Body must not contain the --- delimiters or the YAML keys."""
        from streamlit_app.data import parsers

        p = tmp_path / "doc.md"
        p.write_text("---\ntitle: test\nauthor: me\n---\n# Heading\n", encoding="utf-8")

        _meta, body = parsers.parse_frontmatter(p)

        assert "---" not in body
        assert "title:" not in body
        assert "author:" not in body
        assert "# Heading" in body

    def test_handles_real_adr(self, tmp_path: Path) -> None:
        """Parsing a real ADR draft returns the expected frontmatter fields."""
        from streamlit_app.data import parsers

        real = _real_adr_path()
        if not real.exists():
            pytest.skip("Real ADR draft not found in worktree — skipping")

        dest = tmp_path / real.name
        dest.write_bytes(real.read_bytes())

        meta, body = parsers.parse_frontmatter(dest)

        # All standard ADR frontmatter keys must be present
        for key in ("id", "title", "status", "category", "date", "summary", "made_by"):
            assert key in meta, f"Expected frontmatter key '{key}' not found"

        # id must follow the draft pattern
        assert str(meta["id"]).startswith("dec-draft-")

    def test_raises_file_not_found_on_absent_path(self, tmp_path: Path) -> None:
        """parse_frontmatter raises FileNotFoundError when the path does not exist."""
        from streamlit_app.data import parsers

        with pytest.raises(FileNotFoundError):
            parsers.parse_frontmatter(tmp_path / "missing.md")


# ---------------------------------------------------------------------------
# Group 2 — parse_yaml
# ---------------------------------------------------------------------------


class TestParseYaml:
    def test_parses_dict_yaml(self, tmp_path: Path) -> None:
        """A YAML file containing a mapping is parsed into a dict."""
        from streamlit_app.data import parsers

        p = tmp_path / "config.yml"
        p.write_text("key: value\nnumber: 7\n", encoding="utf-8")

        result = parsers.parse_yaml(p)

        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["number"] == 7

    def test_parses_list_yaml(self, tmp_path: Path) -> None:
        """A YAML file containing a sequence is parsed into a list."""
        from streamlit_app.data import parsers

        p = tmp_path / "list.yml"
        p.write_text("- a\n- b\n- c\n", encoding="utf-8")

        result = parsers.parse_yaml(p)

        assert isinstance(result, list)
        assert result == ["a", "b", "c"]

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        """parse_yaml raises FileNotFoundError when the file does not exist."""
        from streamlit_app.data import parsers

        with pytest.raises(FileNotFoundError):
            parsers.parse_yaml(tmp_path / "nonexistent.yml")

    def test_raises_on_malformed_yaml(self, tmp_path: Path) -> None:
        """parse_yaml raises yaml.YAMLError on invalid YAML content."""
        import yaml

        from streamlit_app.data import parsers

        p = tmp_path / "bad.yml"
        p.write_text("key: [unclosed\n", encoding="utf-8")

        with pytest.raises(yaml.YAMLError):
            parsers.parse_yaml(p)


# ---------------------------------------------------------------------------
# Group 3 — parse_md_sections
# ---------------------------------------------------------------------------


class TestParseMdSections:
    def test_splits_by_h2_default(self, tmp_path: Path) -> None:
        """Level-2 headings are the split points by default."""
        from streamlit_app.data import parsers

        p = tmp_path / "doc.md"
        p.write_text("## Foo\nA line\n## Bar\nB line\n", encoding="utf-8")

        sections = parsers.parse_md_sections(p)

        assert "Foo" in sections
        assert "Bar" in sections
        assert "A line" in sections["Foo"]
        assert "B line" in sections["Bar"]

    def test_content_before_first_heading_under_empty_key(self, tmp_path: Path) -> None:
        """Content before the first heading is stored under the '' key."""
        from streamlit_app.data import parsers

        p = tmp_path / "doc.md"
        p.write_text("preamble\n\n## Section\nbody\n", encoding="utf-8")

        sections = parsers.parse_md_sections(p)

        assert "" in sections
        assert "preamble" in sections[""]

    def test_level_3_when_specified(self, tmp_path: Path) -> None:
        """level=3 splits on ### headings, ignoring ## headings."""
        from streamlit_app.data import parsers

        p = tmp_path / "doc.md"
        p.write_text("## Big\n### Small\ncontent\n", encoding="utf-8")

        sections = parsers.parse_md_sections(p, level=3)

        assert "Small" in sections
        # "Big" is a level-2 heading — not split at level=3
        assert "Big" not in sections

    def test_does_not_split_on_lower_levels(self, tmp_path: Path) -> None:
        """### sub-headings inside a ## section stay inside the section body."""
        from streamlit_app.data import parsers

        p = tmp_path / "doc.md"
        p.write_text("## Parent\ntext\n### Sub\nmore text\n", encoding="utf-8")

        sections = parsers.parse_md_sections(p)  # default level=2

        assert "Parent" in sections
        # Sub-heading and its content should be in the Parent section body
        assert "Sub" in sections["Parent"] or "more text" in sections["Parent"]
        # No top-level key for "Sub" when splitting at level=2
        assert "Sub" not in sections

    def test_handles_real_architecture_md(self, tmp_path: Path) -> None:
        """Parsing the real ARCHITECTURE.md yields expected section names."""
        from streamlit_app.data import parsers

        real = Path(__file__).parent.parent.parent / ".ai-state" / "ARCHITECTURE.md"
        if not real.exists():
            pytest.skip("ARCHITECTURE.md not found — skipping")

        dest = tmp_path / "ARCHITECTURE.md"
        dest.write_bytes(real.read_bytes())

        sections = parsers.parse_md_sections(dest, level=2)

        # ARCHITECTURE.md has known top-level sections
        section_names = set(sections.keys())
        assert any(
            "Overview" in name or "Components" in name or "System Context" in name
            for name in section_names
        ), f"Expected known section names, got: {section_names}"

    def test_raises_file_not_found_on_absent_path(self, tmp_path: Path) -> None:
        """parse_md_sections raises FileNotFoundError when the file is absent."""
        from streamlit_app.data import parsers

        with pytest.raises(FileNotFoundError):
            parsers.parse_md_sections(tmp_path / "gone.md")


# ---------------------------------------------------------------------------
# Group 4 — parse_metrics_log
# ---------------------------------------------------------------------------

# Minimal two-column Markdown table for METRICS_LOG.md tests.
_METRICS_LOG_TWO_ROWS = """\
| timestamp | report_file |
| --- | --- |
| 2026-01-01T00:00:00Z | METRICS_REPORT_2026-01-01.md |
| 2026-01-02T00:00:00Z | METRICS_REPORT_2026-01-02.md |
"""


class TestParseMetricsLog:
    def test_returns_empty_df_on_missing_file(self, tmp_path: Path) -> None:
        """parse_metrics_log returns an empty DataFrame when the file is absent."""
        from streamlit_app.data import parsers

        result = parsers.parse_metrics_log(tmp_path / "nonexistent.md")

        assert result.empty

    def test_parses_simple_table(self, tmp_path: Path) -> None:
        """A two-row Markdown table is parsed into a DataFrame with 2 rows."""
        from streamlit_app.data import parsers

        p = tmp_path / "METRICS_LOG.md"
        p.write_text(_METRICS_LOG_TWO_ROWS, encoding="utf-8")

        df = parsers.parse_metrics_log(p)

        assert len(df) == 2
        assert "timestamp" in df.columns
        assert df["report_file"].iloc[0] == "METRICS_REPORT_2026-01-01.md"

    def test_skips_separator_row(self, tmp_path: Path) -> None:
        """The Markdown table separator row (|---|---) must not appear as a data row."""
        from streamlit_app.data import parsers

        p = tmp_path / "METRICS_LOG.md"
        p.write_text(_METRICS_LOG_TWO_ROWS, encoding="utf-8")

        df = parsers.parse_metrics_log(p)

        # Verify the separator is not in the data
        for col in df.columns:
            for val in df[col].astype(str):
                assert "---" not in val, f"Separator found in column '{col}': {val!r}"


# ---------------------------------------------------------------------------
# Group 5 — parse_metrics_report_json
# ---------------------------------------------------------------------------


class TestParseMetricsReportJson:
    def test_parses_valid_json(self, tmp_path: Path) -> None:
        """A well-formed JSON file is parsed into a dict."""
        from streamlit_app.data import parsers

        p = tmp_path / "METRICS_REPORT_2026-01-01.json"
        p.write_text(
            json.dumps({"schema_version": "1.0.0", "score": 42}), encoding="utf-8"
        )

        result = parsers.parse_metrics_report_json(p)

        assert isinstance(result, dict)
        assert result["schema_version"] == "1.0.0"
        assert result["score"] == 42

    def test_raises_on_malformed_json(self, tmp_path: Path) -> None:
        """Malformed JSON raises json.JSONDecodeError."""
        from streamlit_app.data import parsers

        p = tmp_path / "bad.json"
        p.write_text("{not valid json", encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            parsers.parse_metrics_report_json(p)

    def test_warns_on_missing_schema_version_but_returns_dict(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """JSON without schema_version emits a WARNING log but still returns the dict."""  # noqa: E501
        from streamlit_app.data import parsers

        p = tmp_path / "no_schema.json"
        p.write_text(json.dumps({"data": "here"}), encoding="utf-8")

        with caplog.at_level(logging.WARNING):
            result = parsers.parse_metrics_report_json(p)

        # Function must still return the parsed dict
        assert isinstance(result, dict)
        assert result["data"] == "here"

        # A WARNING must have been emitted
        assert any(
            "schema_version" in record.message.lower()
            for record in caplog.records
            if record.levelno >= logging.WARNING
        ), (
            "Expected a warning about schema_version; got records: "
            f"{[r.message for r in caplog.records]}"
        )

    def test_raises_file_not_found_on_absent_path(self, tmp_path: Path) -> None:
        """parse_metrics_report_json raises FileNotFoundError when the file is absent."""  # noqa: E501
        from streamlit_app.data import parsers

        with pytest.raises(FileNotFoundError):
            parsers.parse_metrics_report_json(tmp_path / "missing.json")


# ---------------------------------------------------------------------------
# Group 6 — parse_sentinel_log
# ---------------------------------------------------------------------------

_SENTINEL_LOG_TABLE = """\
| timestamp | report_file | health_grade | finding_counts | coherence_grade |
| --- | --- | --- | --- | --- |
| 2026-01-01T00:00:00Z | SENTINEL_REPORT_2026-01-01_00-00-00.md | A | 0 | A |
| 2026-01-02T00:00:00Z | SENTINEL_REPORT_2026-01-02_00-00-00.md | B | 3 | A |
"""


class TestParseSentinelLog:
    def test_returns_empty_df_on_missing_file(self, tmp_path: Path) -> None:
        """parse_sentinel_log returns an empty DataFrame when the file is absent."""
        from streamlit_app.data import parsers

        result = parsers.parse_sentinel_log(tmp_path / "SENTINEL_LOG.md")

        assert result.empty

    def test_parses_table_with_health_grade_column(self, tmp_path: Path) -> None:
        """SENTINEL_LOG.md rows are parsed; health_grade column is present."""
        from streamlit_app.data import parsers

        p = tmp_path / "SENTINEL_LOG.md"
        p.write_text(_SENTINEL_LOG_TABLE, encoding="utf-8")

        df = parsers.parse_sentinel_log(p)

        assert len(df) == 2
        assert "health_grade" in df.columns
        assert df["health_grade"].iloc[0] == "A"


# ---------------------------------------------------------------------------
# Group 7 — parse_wip
# ---------------------------------------------------------------------------


class TestParseWip:
    def test_parses_real_wip_md(self, tmp_path: Path) -> None:
        """Parsing the actual pipeline WIP.md yields structured data."""
        from streamlit_app.data import parsers

        real = (
            Path(__file__).parent.parent.parent
            / ".ai-work"
            / "pipeline-dashboard"
            / "WIP.md"
        )
        if not real.exists():
            pytest.skip("WIP.md not found — skipping")

        dest = tmp_path / "WIP.md"
        dest.write_bytes(real.read_bytes())

        result = parsers.parse_wip(dest)

        # Structural keys must be present
        assert "current_step" in result
        assert "status" in result
        assert "progress" in result

        assert result["current_step"] != "", (
            "current_step should be non-empty for an active WIP"
        )
        assert isinstance(result["progress"], list)
        assert len(result["progress"]) > 0, "progress list should contain steps"

        # At least one step must be marked done (Steps 1a through 3c are complete)
        done_steps = [item for item in result["progress"] if item.get("done")]
        assert len(done_steps) > 0, "Expected at least one completed step"

    def test_returns_empty_skeleton_on_missing_file(self, tmp_path: Path) -> None:
        """parse_wip returns a minimal dict with empty fields when the file is absent."""  # noqa: E501
        from streamlit_app.data import parsers

        result = parsers.parse_wip(tmp_path / "WIP.md")

        assert isinstance(result, dict)
        assert "current_step" in result
        assert result["current_step"] == ""
        assert "progress" in result
        assert isinstance(result["progress"], list)


# ---------------------------------------------------------------------------
# Group 8 — parse_progress
# ---------------------------------------------------------------------------

_VALID_PROGRESS_LINE = (
    "[2026-05-07T19:00:00Z] [systems-architect] Phase 5/10: [trade-offs] "
    "-- ADRs drafted #adrs-drafted #count=10"
)

_MALFORMED_LINES = [
    "not a progress line at all",
    "[ badly formed ] [ no phase ]",
    "",
    "2026-05-07 missing brackets",
]


class TestParseProgress:
    def test_parses_event_line(self, tmp_path: Path) -> None:
        """A well-formed PROGRESS.md line is parsed into an event dict."""
        from streamlit_app.data import parsers

        p = tmp_path / "PROGRESS.md"
        p.write_text(_VALID_PROGRESS_LINE + "\n", encoding="utf-8")

        events = parsers.parse_progress(p)

        assert len(events) == 1
        event = events[0]

        assert "timestamp" in event
        assert event["timestamp"] == "2026-05-07T19:00:00Z"

        assert "agent" in event
        assert event["agent"] == "systems-architect"

        assert "phase" in event
        # Phase field should reference "5/10" or the phase name
        assert "5" in str(event["phase"]) or "trade-offs" in str(
            event.get("summary", "")
        )

        assert "summary" in event
        assert "ADRs drafted" in event["summary"]

        assert "labels" in event
        assert "adrs-drafted" in event["labels"]

        assert "kv" in event
        assert event["kv"].get("count") == "10"

    def test_returns_empty_list_on_missing_file(self, tmp_path: Path) -> None:
        """parse_progress returns [] when the PROGRESS.md file is absent."""
        from streamlit_app.data import parsers

        result = parsers.parse_progress(tmp_path / "PROGRESS.md")

        assert result == []

    def test_skips_malformed_lines(self, tmp_path: Path) -> None:
        """Lines that do not match the progress format are skipped gracefully."""
        from streamlit_app.data import parsers

        content = "\n".join(_MALFORMED_LINES) + "\n" + _VALID_PROGRESS_LINE + "\n"
        p = tmp_path / "PROGRESS.md"
        p.write_text(content, encoding="utf-8")

        events = parsers.parse_progress(p)

        # Only the valid line produces an event
        assert len(events) == 1
        assert events[0]["agent"] == "systems-architect"


# ---------------------------------------------------------------------------
# Group 9 — Convention 1 purity (no Streamlit rendering in parsers.py)
# ---------------------------------------------------------------------------


class TestParsersModulePurity:
    def test_parsers_module_imports_no_streamlit_rendering(self) -> None:
        """parsers.py must not import any Streamlit rendering primitive.

        The data layer is allowed st.cache_data only (in cache.py);
        parsers.py needs no Streamlit imports at all.

        Verified via AST parse — does not require executing the module.
        """
        parsers_path = Path(__file__).parent.parent / "data" / "parsers.py"
        assert parsers_path.exists(), (
            f"parsers.py not found at {parsers_path}; "
            "cannot verify purity without the source file"
        )
        source = parsers_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(parsers_path))

        forbidden_imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "streamlit" or alias.name.startswith("streamlit."):
                        forbidden_imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module == "streamlit" or module.startswith("streamlit."):
                    # Only st.cache_data is tolerated in data/ modules (in cache.py).
                    # parsers.py has no legitimate Streamlit import.
                    for alias in node.names:
                        forbidden_imports.append(f"from {module} import {alias.name}")

        assert forbidden_imports == [], (
            f"parsers.py contains forbidden Streamlit imports "
            f"(Convention 1 — pure data layer): {forbidden_imports}"
        )
