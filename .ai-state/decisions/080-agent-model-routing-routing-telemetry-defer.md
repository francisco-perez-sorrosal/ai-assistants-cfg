---
id: dec-080
title: Defer routing telemetry — ship v1 without transcript-scraping
status: accepted
category: architectural
date: 2026-04-25
summary: No routing-telemetry code in v1; rely on research-grounded heuristics and operator feedback. One-month review triggers reconsideration
tags: [model-routing, telemetry, measure-before-optimize, deferred, observability]
made_by: agent
agent_type: systems-architect
pipeline_tier: standard
affected_files:
  - rules/swe/agent-model-routing.md
affected_reqs:
  - AC1
---

## Context

Claude Code does not document a programmatic API to read the *resolved* model of a spawned subagent. Cost attribution and routing-policy verification today require transcript-scraping: parsing `~/.claude/projects/{project}/{sessionId}/subagents/agent-{id}.jsonl`. The research findings flag this as an open question for the architect. Praxion's "measure-before-optimize" principle pushes toward building the telemetry loop now, but the cost of maintaining scraper code is non-trivial, and the gap is a documented Claude Code deficiency likely to be closed in a future release.

## Decision

Defer all routing-telemetry code in v1. Ship the policy with:

- Research-grounded tier assignments (feasibility verdict, benchmark-cliff identification, Anthropic's own use-case guidance).
- The operator kill switch (`CLAUDE_CODE_SUBAGENT_MODEL`) as the emergency lever if the policy proves wrong.
- A one-month review built into the rule doc (comment in the header) triggering reconsideration if (a) pipelines show quality regressions, (b) cost monitoring at the account level shows the policy under-saving, or (c) Anthropic still has no programmatic resolved-model API.

If the deferred telemetry is needed later, transcript-scraping is straightforward (~100 lines of Python + jsonl parsing). The decision is about *timing*, not feasibility.

## Considered Options

### Option 1 — Build transcript-scraping now

- Pros: Direct evidence the policy works as designed; closes the loop before we need it; aligns with "measure before optimize."
- Cons: Maintenance burden for code that a Claude Code API will likely replace. Delays policy ship by 1–2 weeks.

### Option 2 — Defer telemetry (selected)

- Pros: Ships fast; zero scraper-maintenance cost; leverages existing research verdict as ground truth; operator kill switch is the immediate lever.
- Cons: No direct evidence the policy works. Relies on verifier + sentinel + user feedback to surface regressions indirectly.

## Consequences

**Positive:**

- Days-not-weeks to ship the policy.
- No transient scraper code to deprecate when Anthropic ships a resolved-model API.
- Aligns with "measure *before* 2D optimization" — v1 is the baseline to compare against, not the measured optimum.

**Negative:**

- We cannot claim the 30–50% savings figure with confidence until after the fact.
- Silent mis-routing (policy says Sonnet but spawn lands on Haiku due to `availableModels` rejection) is not auto-detected.

**Risks accepted:**

- Deferral-bet loses if Anthropic does not ship the API. Mitigated: transcript-scraping is a follow-up Lightweight task if the bet loses.
- Regressions surface through user pain rather than metrics. Mitigated by the operator kill switch and the one-month review cadence.
