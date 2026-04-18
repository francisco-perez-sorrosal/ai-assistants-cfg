# Calibration Log

Append-only tier-selection log. Each Standard/Full pipeline (and every tier on completion) appends one row so the sentinel can analyze recommendation-vs-actual match rate (CA01/CA02) over time. See `rules/swe/swe-agent-coordination-protocol.md` and `rules/swe/agent-intermediate-documents.md`.

| Timestamp | Task | Signals | Recommended Tier | Actual Tier | Source | Retrospective |
|-----------|------|---------|------------------|-------------|--------|----------------|
