---
id: dec-018
title: Opinionated tool defaults in deployment skill decision framework
status: accepted
category: architectural
date: 2026-04-06
summary: Deployment skill recommends specific tools as defaults (Caddy, Railway/Render, Ollama, gunicorn+uvicorn) rather than presenting all options equally
tags: [deployment, skill-design, decision-framework, opinionated]
made_by: agent
agent_type: systems-architect
pipeline_tier: standard
affected_files:
  - skills/deployment/SKILL.md
---

## Context

The deployment landscape has 20+ viable tools across 6 categories. Research findings identified "tool selection paralysis" as the #1 gap an AI-assisted deployment skill can address. The skill's decision framework must either present options neutrally or make specific recommendations.

## Decision

The decision framework makes opinionated default recommendations backed by research:
- **Reverse proxy**: Caddy (simplest auto-HTTPS) over nginx or Traefik
- **PaaS for beginners**: Railway or Render over Fly.io (less operational complexity)
- **Local AI/ML**: Ollama for dev (simplicity) over vLLM (throughput)
- **Python production server**: gunicorn + uvicorn over standalone uvicorn
- **GPU in the cloud**: Modal for simplicity over CoreWeave (K8s familiarity required)
- **Secrets for teams**: SOPS + age over 1Password CLI (free, git-friendly)

Alternatives are always mentioned alongside defaults. Defaults are framed as "start here" not "only option."

## Considered Options

### Option 1: Neutral comparison tables

Present all tools with pros/cons columns. Let the user decide.

Pros: No controversy, comprehensive, feels objective.

Cons: Does not solve the decision paralysis problem. Users who want guidance must still evaluate trade-offs themselves. Comparison tables exist everywhere on the internet already.

### Option 2: Opinionated defaults with alternatives (chosen)

Recommend a specific tool as the default for each decision point. Explain why. Always mention alternatives for users with different constraints.

Pros: Solves decision paralysis. Provides actionable guidance. Research-backed rationale available for each choice.

Cons: Defaults can become stale. Users who disagree with defaults may feel the skill is biased. Requires periodic review.

## Consequences

**Positive:**
- Users get actionable guidance instead of more comparison tables
- Reduced decision fatigue for the most common deployment scenarios
- Research backing for each default provides credibility and updateability

**Negative:**
- Defaults will need periodic review as the landscape evolves (e.g., TGI already deprecated)
- Power users may feel the skill is too prescriptive (mitigated by always showing alternatives)
- Vendor changes (pricing, features, shutdowns) can invalidate recommendations quickly
