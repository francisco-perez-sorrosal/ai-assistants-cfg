"""Render a CLAUDE.md template by substituting personal-info placeholders.

Extracted from the inline Python heredoc in install_claude.sh:223 to allow
reuse by both install_claude.sh (clone-install flow) and
hooks/auto_complete_install.py (first-session auto-install flow).

Public API:

    render_claude_md(template_path, output_path, values) -> None
    derive_defaults() -> dict[str, str]

Placeholders handled: {{USERNAME}}, {{EMAIL}}, {{GITHUB_URL}}
Residual placeholders (unknown keys) are logged to stderr but do not raise.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PLACEHOLDER_PATTERN = re.compile(r"\{\{[A-Z_]+\}\}")

_FALLBACK_EMAIL = "anon@unknown"
_FALLBACK_USERNAME = "@anon"
_FALLBACK_GITHUB_URL = "https://github.com/anon"


# ---------------------------------------------------------------------------
# Core render function
# ---------------------------------------------------------------------------


def render_claude_md(
    template_path: Path,
    output_path: Path,
    values: dict[str, str],
) -> None:
    """Render template_path into output_path by substituting {{KEY}} placeholders.

    Args:
        template_path: Path to the source template file.  Must exist.
        output_path: Destination path.  Parent directories are created if needed.
        values: Mapping of placeholder names (without braces) to replacement
                strings.  Unrecognised placeholders are logged to stderr and
                left in the output rather than raising.

    Raises:
        FileNotFoundError: When template_path does not exist.
        OSError: On any other I/O failure reading or writing files.
    """
    content = template_path.read_text(encoding="utf-8")

    for key, replacement in values.items():
        content = content.replace(f"{{{{{key}}}}}", replacement)

    residuals = PLACEHOLDER_PATTERN.findall(content)
    if residuals:
        unique = sorted(set(residuals))
        print(
            f"Warning: render_claude_md: residual placeholders after substitution: "
            f"{', '.join(unique)}",
            file=sys.stderr,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Default-value derivation
# ---------------------------------------------------------------------------


def _run_git_config(key: str) -> str | None:
    """Run `git config <key>` and return stripped stdout, or None on failure."""
    result = subprocess.run(
        ["git", "config", key],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value if value else None


def _sanitize_slug(raw: str) -> str:
    """Lowercase and strip non-alphanumeric characters from a string.

    Non-alphanumeric runs are replaced with a single hyphen; leading/trailing
    hyphens are removed.  The result is safe for use in URLs and filenames.
    """
    lowered = raw.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "anon"


def derive_defaults() -> dict[str, str]:
    """Derive personal-info substitution defaults from git config.

    Reads git config user.email to derive all three values.  Falls back to
    safe placeholder strings when git config is absent or unavailable.

    Returns:
        A dict with keys USERNAME, EMAIL, and GITHUB_URL.
    """
    email = _run_git_config("user.email")

    if not email:
        return {
            "USERNAME": _FALLBACK_USERNAME,
            "EMAIL": _FALLBACK_EMAIL,
            "GITHUB_URL": _FALLBACK_GITHUB_URL,
        }

    local_part = email.split("@")[0] if "@" in email else email
    slug = _sanitize_slug(local_part)
    username = f"@{slug}"

    return {
        "USERNAME": username,
        "EMAIL": email,
        "GITHUB_URL": f"https://github.com/{slug}",
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _main(argv: list[str] | None = None) -> int:
    """CLI: render_claude_md.py <template> <output> [USERNAME EMAIL GITHUB_URL]."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Render a CLAUDE.md template with personal-info substitution."
    )
    parser.add_argument("template", type=Path, help="Source template path")
    parser.add_argument("output", type=Path, help="Destination output path")
    parser.add_argument("username", nargs="?", help="{{USERNAME}} value")
    parser.add_argument("email", nargs="?", help="{{EMAIL}} value")
    parser.add_argument("github_url", nargs="?", help="{{GITHUB_URL}} value")

    args = parser.parse_args(argv)

    if args.username or args.email or args.github_url:
        values = {
            "USERNAME": args.username or "",
            "EMAIL": args.email or "",
            "GITHUB_URL": args.github_url or "",
        }
    else:
        values = derive_defaults()

    try:
        render_claude_md(args.template, args.output, values)
    except (FileNotFoundError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(_main())
