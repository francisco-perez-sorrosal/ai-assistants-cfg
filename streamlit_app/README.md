# Praxion Pipeline Dashboard

A multi-page Streamlit control room for Praxion-onboarded projects.  Turns
each project's `.ai-state/` and `.ai-work/` filesystem into a visual,
educational entry point covering architecture, in-flight workshops, ADRs,
sentinel health, roadmap, and metrics.

**Read-only.** The dashboard never writes to `.ai-state/` or `.ai-work/`,
calls no external APIs, and makes no LLM calls.

---

## Install

```bash
# One-time install per user (creates ~/.praxion-dashboard/venv/)
scripts/praxion-dashboard install
```

Requirements: Python 3.11+, macOS (v1; Linux manual-launch supported).

## Run

```bash
# Via lifecycle ctl (recommended)
scripts/praxion-dashboard start /path/to/project

# Or directly (dev mode)
PRAXION_PROJECT_ROOT=/path/to/project streamlit run streamlit_app/app.py
```

The port is derived deterministically from the project root path
(sha256-based, range 8501–9500), so the URL is stable across restarts.

## Lifecycle commands

```
praxion-dashboard install    # create venv, install deps, register launchd plist
praxion-dashboard start      # launch Streamlit and open browser
praxion-dashboard stop       # terminate the running process
praxion-dashboard restart    # stop + start
praxion-dashboard status     # show running/stopped + URL
praxion-dashboard uninstall  # remove plist and venv
```

## Pages

| Page           | Source artifacts                                  | REQ   |
|----------------|---------------------------------------------------|-------|
| Architecture   | `.ai-state/ARCHITECTURE.md` + LikeC4 SVG         | REQ-03 |
| Workshops      | `.ai-work/<slug>/WIP.md` + `PROGRESS.md`          | REQ-04, REQ-05 |
| ADRs           | `.ai-state/decisions/` (finalized + drafts)       | REQ-06 |
| Sentinel       | `.ai-state/sentinel_reports/`                     | REQ-07 |
| Roadmap        | `ROADMAP.md`                                      | REQ-08 |
| Metrics        | `.ai-state/metrics_reports/`                      | REQ-09 |

All pages degrade gracefully to an empty-state widget when their source
artifact is absent.

## Key constraints

- **Single install, per-project usage**: set `PRAXION_PROJECT_ROOT` to select
  the project; the app never uses `os.getcwd()` as the root.
- **No data writing**: purely read-only filesystem access.
- **Auto-refresh on Workshops only**: uses `st.fragment(run_every=)` (default
  15 s, override via `PRAXION_DASHBOARD_POLL_SECONDS`).  Other pages require
  a manual browser refresh.
- **No Mermaid in v1**: deferred to v2 per ADR dec-draft-d57dc712.

## Development

```bash
# Run tests
python -m pytest streamlit_app/tests/ -v

# Verify data layer isolation (no rendering primitives in discovery/parsers)
grep -r "^import streamlit\|^from streamlit" streamlit_app/data/
# Expected: only cache.py appears

# Shell lifecycle tests
bash streamlit_app/tests/test_ctl.sh
```

## Package layout

```
streamlit_app/
  app.py          — Streamlit entrypoint (Step 2a)
  launcher.py     — subprocess wrapper (Step 14a)
  config.py       — env var reader (Step 2a)
  data/
    discovery.py  — filesystem discovery (Step 3a)
    parsers.py    — pure parsing functions (Step 4a)
    cache.py      — @st.cache_data wrappers (Step 5a)
  pages/
    architecture.py  (Step 10a)
    workshops.py     (Step 7a)
    adrs.py          (Step 8a)
    sentinel.py      (Step 9a)
    roadmap.py       (Step 11a)
    metrics.py       (Step 12a)
  widgets/
    artifact_card.py   (Step 6a)
    educational.py     (Step 6a)
    graph.py           (Step 6a)
    empty_state.py     (Step 6a)
  tests/
    conftest.py
    test_discovery.py  test_parsers.py  test_cache.py
    test_widgets.py
    test_page_*.py  (one per page)
    test_e2e_smoke.py
    test_ctl.sh
```

## Links

- Coordination protocol: `rules/swe/swe-agent-coordination-protocol.md`
- ADR conventions: `rules/swe/adr-conventions.md`
- Dashboard conventions: `rules/swe/dashboard-conventions.md`
- Architecture as code: `skills/architecture-as-code/SKILL.md`
