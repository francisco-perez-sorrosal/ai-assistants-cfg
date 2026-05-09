"""Shared helpers used by multiple component renderers.

Renderers should NOT duplicate frontmatter parsing, MD body extraction, or
anchor-link mechanics — import from here.

Pure-Python; no Streamlit imports (so this module can be tested without a
Streamlit context). The render-side helpers that need `st` live inline in
each renderer.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from streamlit_app.data.parsers import parse_frontmatter


# ---------------------------------------------------------------------------
# Frontmatter + body extraction
# ---------------------------------------------------------------------------


def read_md(path: Path) -> tuple[dict[str, Any], str]:
    """Read a markdown file, returning (frontmatter, body).

    Body has the frontmatter block stripped. If no frontmatter is present,
    returns ({}, full_text). Raises FileNotFoundError if the file is missing.
    """
    return parse_frontmatter(path)


def extract_first_h1(body: str) -> str | None:
    """Return the text of the first H1 heading in `body`, or None."""
    m = re.search(r"^#\s+(.+?)\s*$", body, re.MULTILINE)
    return m.group(1).strip() if m else None


def extract_first_paragraph(body: str) -> str | None:
    """Return the first non-heading paragraph in `body` (truncated to 280 chars)."""
    # Split into blocks by blank lines; first block that doesn't start with `#`.
    for block in re.split(r"\n\s*\n", body.strip()):
        block = block.strip()
        if block and not block.startswith("#"):
            # Collapse internal whitespace and clip
            text = re.sub(r"\s+", " ", block)
            return text[:280] + ("..." if len(text) > 280 else "")
    return None


# ---------------------------------------------------------------------------
# H2 section extraction (used by tutorial_shell to find numbered steps)
# ---------------------------------------------------------------------------


def split_h2_sections(body: str) -> list[tuple[str, str]]:
    """Split `body` into (h2_title, h2_body) pairs.

    Content before the first H2 is returned with title "". H2s with no body
    text are returned with body "".
    """
    parts: list[tuple[str, str]] = []
    pattern = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(body))
    if not matches:
        return [("", body.strip())]

    # Pre-H2 content (if any)
    if matches[0].start() > 0:
        pre = body[: matches[0].start()].strip()
        if pre:
            parts.append(("", pre))

    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        section_body = body[start:end].strip()
        parts.append((title, section_body))
    return parts


# ---------------------------------------------------------------------------
# H3 step extraction (for plan_view IMPLEMENTATION_PLAN.md parsing)
# ---------------------------------------------------------------------------


def split_h3_sections(body: str) -> list[tuple[str, str]]:
    """Like `split_h2_sections`, but for H3 — used to extract steps from
    plan-style docs (IMPLEMENTATION_PLAN.md uses `### Step N:` headings)."""
    parts: list[tuple[str, str]] = []
    pattern = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(body))
    if not matches:
        return [("", body.strip())]

    if matches[0].start() > 0:
        pre = body[: matches[0].start()].strip()
        if pre:
            parts.append(("", pre))

    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        section_body = body[start:end].strip()
        parts.append((title, section_body))
    return parts


# ---------------------------------------------------------------------------
# Markdown anchor helper
# ---------------------------------------------------------------------------


def heading_to_anchor(heading: str) -> str:
    """GitHub-style anchor slug for an H2/H3 heading.

    Lowercase, alphanumerics + hyphens; collapse other chars to hyphens.
    """
    slug = heading.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = slug.strip("-")
    return slug


# ---------------------------------------------------------------------------
# Surface descriptor convenience accessors
# ---------------------------------------------------------------------------


def surface_title(surface: dict[str, Any], body: str | None = None) -> str:
    """Return the human-facing title for a surface.

    Priority: explicit `surface["title"]` → first H1 in body → surface id.
    """
    if surface.get("title"):
        return str(surface["title"])
    if body is not None:
        h1 = extract_first_h1(body)
        if h1:
            return h1
    return str(surface.get("id", "(untitled)"))


def surface_summary(surface: dict[str, Any], body: str | None = None) -> str | None:
    """Return the summary for a surface.

    Priority: explicit `surface["summary"]` → first paragraph of body → None.
    """
    if surface.get("summary"):
        return str(surface["summary"])
    if body is not None:
        return extract_first_paragraph(body)
    return None


__all__ = [
    "read_md",
    "extract_first_h1",
    "extract_first_paragraph",
    "split_h2_sections",
    "split_h3_sections",
    "heading_to_anchor",
    "surface_title",
    "surface_summary",
]
