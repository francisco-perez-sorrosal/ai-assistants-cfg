"""Smoke tests for `streamlit_app/components/` renderers.

Each renderer in the registry is dispatched against the first real on-disk
surface that the manifest assigns it, under `AppTest`. Catches the class
of bug that broke every Tier-2 renderer during the doc-strategy session:
schema-assumption mismatches against real surfaces (trailing-prose bullet
parsers, regex group-index errors, f-string lint slips). Each renderer
that shipped that session was caught by manual smoke against real
surfaces — codifying that prevents regression.

Tests skip gracefully when:
- The manifest has no surface assigned to the renderer (fork projects
  may legitimately have zero ADRs, zero proposals, etc.)
- The surface's source path does not exist on disk (`.ai-work/` is
  gitignored, so CI checkouts may not have transient surfaces)

The renderer's own missing-file handling (`if not path.exists():
st.error(...)`) is NOT an exception, so the smoke test would pass even
without the skip — but skipping is cleaner because a missing-file error
display is not what we want to verify.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from streamlit.testing.v1 import AppTest


# Praxion repo root: streamlit_app/tests/test_X.py → repo root.
_PRAXION_ROOT = Path(__file__).resolve().parent.parent.parent
_MANIFEST = _PRAXION_ROOT / ".ai-state" / "doc_manifest.yaml"


# Every renderer the registry exposes; data-driven over parametrize so each
# renderer gets its own pass/fail line in the report.
_RENDERERS = [
    "default_markdown",
    "tutorial_shell",
    "plan_view",
    "adr_card",
    "reference_shell",
    "explanation_shell",
    "how_to_shell",
    "verification_report",
    "idea_grid",
    "architecture_explorer",
    "metrics_view",
]


def _surfaces_for(renderer: str) -> list[dict]:
    if not _MANIFEST.is_file():
        return []
    manifest = yaml.safe_load(_MANIFEST.read_text())
    return [
        s for s in (manifest.get("surfaces") or []) if s.get("renderer") == renderer
    ]


def _build_dispatch_script(surface_id: str) -> str:
    """Build an AppTest script that re-reads the manifest and dispatches
    `surface_id` through the components registry. Reading the manifest
    inside the script (rather than serializing the surface dict) keeps
    the test resilient to surface schema changes — the renderer reads
    whatever the manifest actually carries."""
    return f"""
import yaml
from pathlib import Path
from streamlit_app.components import dispatch

PROJECT_ROOT = Path({str(_PRAXION_ROOT)!r})
manifest = yaml.safe_load(
    (PROJECT_ROOT / ".ai-state" / "doc_manifest.yaml").read_text()
)
surface = next(s for s in manifest["surfaces"] if s["id"] == {surface_id!r})
dispatch(surface, PROJECT_ROOT)
"""


@pytest.mark.parametrize("renderer", _RENDERERS)
def test_renderer_dispatches_against_first_real_surface(renderer: str) -> None:
    surfaces = _surfaces_for(renderer)
    if not surfaces:
        pytest.skip(f"No surfaces with renderer={renderer!r} in manifest")

    surface = surfaces[0]
    surface_path = _PRAXION_ROOT / surface["path"]
    if not surface_path.exists():
        pytest.skip(
            f"Surface {surface['id']!r} references {surface['path']!r} which "
            "does not exist on disk (likely gitignored .ai-work/ content)"
        )

    at = AppTest.from_string(_build_dispatch_script(surface["id"])).run()
    assert not at.exception, (
        f"Renderer {renderer!r} raised when dispatching surface "
        f"{surface['id']!r}: {at.exception}"
    )


def test_registry_covers_all_tier2_renderers() -> None:
    """Every renderer name in the parametrize list must resolve in the
    registry — guards against accidental removal."""
    from streamlit_app.components import list_renderers

    registered = set(list_renderers())
    missing = set(_RENDERERS) - registered
    assert not missing, f"Renderers absent from registry: {sorted(missing)}"


def test_unknown_renderer_falls_back_without_raising() -> None:
    """Unknown renderer names dispatch through `default_markdown` rather
    than crashing the page — guards the documentation page's promise that
    a future renderer name in a manifest can never break the dashboard."""
    script = f"""
from pathlib import Path
from streamlit_app.components import dispatch

surface = {{
    "id": "smoke-unknown",
    "path": "README.md",
    "type": "markdown",
    "renderer": "no_such_renderer_will_ever_exist",
}}
dispatch(surface, Path({str(_PRAXION_ROOT)!r}))
"""
    at = AppTest.from_string(script).run()
    assert not at.exception, f"Unknown-renderer fallback raised: {at.exception}"
