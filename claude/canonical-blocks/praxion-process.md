## Praxion Process

Apply Praxion's tier-driven pipeline for non-trivial work. Use the tier selector from `rules/swe/swe-agent-coordination-protocol.md`: Direct (single-file fix/typo) or Lightweight (2–3 files) may skip the full pipeline; Standard or Full tier work requires researcher → systems-architect → implementation-planner → implementer + test-engineer → verifier.

**Rule-inheritance corollary.** When delegating to any subagent — Praxion-native or host-native (Explore, Plan, general-purpose) — carry the behavioral contract into every delegation prompt. Host-native subagents do not load CLAUDE.md; the orchestrator is the only delivery path.

**Orchestrator obligation.** Every delegation prompt must name the task slug, expected deliverables, and the behavioral contract (Surface Assumptions · Register Objection · Stay Surgical · Simplicity First).
