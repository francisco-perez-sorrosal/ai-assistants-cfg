"""
Praxion Pipeline Dashboard — configuration reader.

Reads PRAXION_PROJECT_ROOT (required) and PRAXION_DASHBOARD_POLL_SECONDS
(optional) from the environment and exposes a cached DashboardConfig dataclass.

Convention compliance
---------------------
  No Streamlit rendering primitives imported here.  Only st.cache_data is
  permitted in the data layer, and it is not needed in this module because
  config is process-scoped (functools.lru_cache is sufficient).

Design constraints
------------------
  - Never hardcode paths.
  - Never assume os.getcwd() equals the project root — always read the env var.
  - mermaid_enabled is deferred to v2; the field is present but always False
    in v1 regardless of any user toggle.
"""

from __future__ import annotations

import logging
import os
import tomllib
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from streamlit_app import __version__

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

_ENV_PROJECT_ROOT = "PRAXION_PROJECT_ROOT"
_ENV_POLL_SECONDS = "PRAXION_DASHBOARD_POLL_SECONDS"
_DEFAULT_POLL_SECONDS = 15
_POLL_MIN = 1
_POLL_MAX = 300


# ── Config dataclass ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class DashboardConfig:
    """Immutable, process-scoped configuration for the dashboard."""

    project_root: Path
    project_name: str
    poll_interval_seconds: int = _DEFAULT_POLL_SECONDS
    mermaid_enabled: bool = False
    dashboard_version: str = field(default_factory=lambda: __version__)


# ── Internal helpers ───────────────────────────────────────────────────────────


def _read_project_root() -> Path:
    raw = os.environ.get(_ENV_PROJECT_ROOT, "").strip()
    if not raw:
        raise ValueError(
            f"Environment variable {_ENV_PROJECT_ROOT!r} is required but not set. "
            "Set it to the absolute path of the target Praxion project before "
            "launching the dashboard:\n"
            f"    {_ENV_PROJECT_ROOT}=/path/to/your/project streamlit run streamlit_app/app.py"
        )
    path = Path(raw)
    if not path.is_absolute():
        raise ValueError(
            f"{_ENV_PROJECT_ROOT}={raw!r} must be an absolute path, got a relative path."
        )
    return path


def _read_poll_seconds() -> int:
    raw = os.environ.get(_ENV_POLL_SECONDS, "").strip()
    if not raw:
        return _DEFAULT_POLL_SECONDS
    try:
        value = int(raw)
    except ValueError:
        logger.warning(
            "%s=%r is not a valid integer; falling back to default %d seconds.",
            _ENV_POLL_SECONDS,
            raw,
            _DEFAULT_POLL_SECONDS,
        )
        return _DEFAULT_POLL_SECONDS
    if not (_POLL_MIN <= value <= _POLL_MAX):
        logger.warning(
            "%s=%d is outside the allowed range [%d, %d]; clamping.",
            _ENV_POLL_SECONDS,
            value,
            _POLL_MIN,
            _POLL_MAX,
        )
        return max(_POLL_MIN, min(_POLL_MAX, value))
    return value


def _read_toml_overrides(project_root: Path) -> dict[str, object]:
    """Read optional poll_interval_seconds override from project TOML config.

    Checks (in order):
      1. <project_root>/.streamlit/config.toml  [dashboard] section
      2. <project_root>/pyproject.toml          [tool.praxion-dashboard] section

    Returns a dict of override values (may be empty).
    """
    # .streamlit/config.toml
    streamlit_config = project_root / ".streamlit" / "config.toml"
    if streamlit_config.is_file():
        try:
            with streamlit_config.open("rb") as fh:
                data = tomllib.load(fh)
            section = data.get("dashboard", {})
            if isinstance(section, dict):
                return section
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not read %s: %s", streamlit_config, exc)

    # pyproject.toml [tool.praxion-dashboard]
    pyproject = project_root / "pyproject.toml"
    if pyproject.is_file():
        try:
            with pyproject.open("rb") as fh:
                data = tomllib.load(fh)
            section = data.get("tool", {}).get("praxion-dashboard", {})
            if isinstance(section, dict):
                return section
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not read %s: %s", pyproject, exc)

    return {}


# ── Public API ─────────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def get_config() -> DashboardConfig:
    """Return the process-scoped dashboard configuration.

    Cached via lru_cache — loads once per process.  Call
    ``get_config.cache_clear()`` in tests to reset.

    Raises
    ------
    ValueError
        When PRAXION_PROJECT_ROOT is absent or not an absolute path.
    """
    project_root = _read_project_root()
    poll_seconds = _read_poll_seconds()

    overrides = _read_toml_overrides(project_root)
    if "poll_interval_seconds" in overrides:
        raw_override = overrides["poll_interval_seconds"]
        try:
            poll_seconds = max(_POLL_MIN, min(_POLL_MAX, int(raw_override)))
        except (TypeError, ValueError):
            logger.warning(
                "TOML poll_interval_seconds=%r is invalid; ignoring.", raw_override
            )

    mermaid_enabled = bool(overrides.get("mermaid_enabled", False))
    if mermaid_enabled:
        logger.warning(
            "mermaid_enabled=true is set but Mermaid rendering is deferred to v2. "
            "The setting will be ignored."
        )
        mermaid_enabled = False

    return DashboardConfig(
        project_root=project_root,
        project_name=project_root.name,
        poll_interval_seconds=poll_seconds,
        mermaid_enabled=False,
        dashboard_version=__version__,
    )
