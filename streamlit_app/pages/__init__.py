"""
Page modules for the Praxion Pipeline Dashboard.

Each page module exports a single top-level `render()` callable.
No import-time execution is allowed in any page module.

Pages
-----
  architecture  — design navigator: ARCHITECTURE.md + LikeC4 SVG 
  workshops     — live-refresh in-flight pipeline monitor 
  adrs          — ADR browser: finalized + draft; filter, detail, supersession 
  sentinel      — sentinel health dashboard: grade, sparkline, dimensions 
  roadmap       — roadmap viewer: ROADMAP.md section reader 
  metrics       — metrics viewer: METRICS_LOG.md + METRICS_REPORT_*.json 

All pages must degrade gracefully (empty-state widget) when their source
artifact is absent or unreadable.
"""
