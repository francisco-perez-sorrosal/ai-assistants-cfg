"""
Data layer for the Praxion Pipeline Dashboard.

Modules in this sub-package are pure Python — no Streamlit rendering
primitives may be imported here, with the **sole exception** of
`st.cache_data` in `cache.py`.

Sub-modules
-----------
  discovery  — filesystem discovery helpers; locates artifacts under
               `PRAXION_PROJECT_ROOT`
  parsers    — pure parsing functions; markdown, YAML frontmatter,
               WIP.md, PROGRESS.md, SENTINEL_LOG.md, METRICS_LOG.md
  cache      — @st.cache_data wrappers with mtime-keyed invalidation
               (the ONLY module permitted to import streamlit)

Convention
----------
The data layer isolation is grep-verifiable:

    grep -r "^import streamlit\\|^from streamlit" streamlit_app/data/

Only `cache.py` should appear in that output.
"""
