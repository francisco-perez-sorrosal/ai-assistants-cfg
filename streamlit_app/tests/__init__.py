"""
Test suite for the Praxion Pipeline Dashboard.

Test modules
------------
  conftest           — shared pytest fixtures (tmp_path project trees, etc.)
  test_discovery     — unit tests for data/discovery.py
  test_parsers       — unit tests for data/parsers.py
  test_cache         — unit tests for data/cache.py
  test_widgets       — widget tests via streamlit.testing.v1
  test_page_workshops  — page tests for pages/workshops.py
  test_page_adrs       — page tests for pages/adrs.py
  test_page_sentinel   — page tests for pages/sentinel.py
  test_page_architecture — page tests for pages/architecture.py
  test_page_roadmap    — page tests for pages/roadmap.py
  test_page_metrics    — page tests for pages/metrics.py
  test_e2e_smoke       — end-to-end smoke test
  test_ctl.sh          — shell tests for scripts/praxion-dashboard
"""
