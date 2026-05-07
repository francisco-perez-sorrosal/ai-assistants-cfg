"""
Praxion Pipeline Dashboard — Streamlit control room.

This package provides a multi-page Streamlit application that renders each
onboarded project's `.ai-state/` and `.ai-work/` filesystem as a visual,
educational control room.

Install model
-------------
One install per user (via `scripts/praxion-dashboard install`), shared across
all Praxion-onboarded projects.  Per-project usage is achieved by pointing to
the project root via the `PRAXION_PROJECT_ROOT` environment variable.

Discovery contract
------------------
  `.ai-state/`  — stateful, persistent, committed to git:
                  ADRs, sentinel reports, metrics, idea ledgers, specs,
                  calibration log, tech-debt ledgers, ARCHITECTURE.md, etc.

  `.ai-work/<slug>/`  — ephemeral, gitignored, deleted after pipeline cleanup:
                        SYSTEMS_PLAN, IMPLEMENTATION_PLAN, WIP, LEARNINGS,
                        TEST_RESULTS, traceability.yml, VERIFICATION_REPORT,
                        PROGRESS, etc.

Read-only contract — v1 never writes
-------------------------------------
The dashboard is **purely read-only**.  It never creates, modifies, or deletes
any artifact in `.ai-state/` or `.ai-work/`.  It makes no external API calls
and no LLM calls.  It is pure Python filesystem rendering.

Transient workshops
-------------------
When `.ai-work/` is empty (between pipeline runs), every page degrades gracefully
to an empty-state widget.  Disappearing Workshops entries are correct, not bugs.
"""

__version__ = "0.1.0-dev"
