---
id: dec-017
title: Local-first Docker Compose as deployment skill gravity center
status: accepted
category: architectural
date: 2026-04-06
summary: Deployment skill uses Docker Compose as primary focus with primitives vocabulary and target-based navigation, not equal-weight comparison of all tools
tags: [deployment, skill-design, docker-compose, local-first]
made_by: agent
agent_type: systems-architect
pipeline_tier: standard
affected_files:
  - skills/deployment/SKILL.md
  - skills/deployment/references/local-deployment.md
---

## Context

The deployment skill covers 6+ deployment target categories (local, PaaS, self-hosted PaaS, serverless, container orchestration, AI-native) with 20+ tools across them. The organizing principle determines how users enter and navigate the skill. Three competing models exist: primitives-first (7 universal concepts), targets-first (6 categories as top-level navigation), or tool-comparison-first (neutral presentation of all options).

Separately, Docker Compose is the de facto standard for local multi-service development, but the skill needs to cover the full spectrum from local to cloud.

## Decision

Use Docker Compose as the skill's gravity center with a three-layer mental model: primitives as vocabulary (compact reference table), targets as navigation (reference files per category), and a decision framework as the primary entry point. SKILL.md dedicates ~120 lines to Docker Compose patterns (the local-first core) while remote targets are reference files loaded on-demand.

## Considered Options

### Option 1: Organize around 7 primitives

Sections for Compute, Networking, Storage, Configuration, Health, Scaling, Dependencies -- each covering how different tools handle that primitive.

Pros: Consistent structure, maps to the universal deployment model, educational.

Cons: Users don't think in primitives -- they think in tasks ("how do I deploy this"). Cross-cutting organization forces users to read multiple sections for one deployment target. Duplicates information across sections.

### Option 2: Equal-weight comparison of all tools

Present all deployment tools equally with comparison tables. No default recommendation.

Pros: Neutral, comprehensive, avoids bias.

Cons: Decision paralysis is the #1 problem in deployment (per research findings). Equal presentation doesn't help users who want guidance. The skill becomes a reference catalog rather than an advisor.

### Option 3: Docker Compose as gravity center with target-based references (chosen)

SKILL.md focuses on Docker Compose as the default local tool. Decision framework routes users to the right target. Target-specific reference files provide depth when needed.

Pros: Clear default for the majority case. Matches the natural progression (local -> remote). Reference files evolve independently. Users get guidance, not just information.

Cons: Users targeting K8s or serverless from day one must navigate to reference files. Docker Compose has a local-only reputation.

## Consequences

**Positive:**
- Users have a clear starting point (Docker Compose) rather than needing to evaluate 20+ tools
- The skill's structure mirrors how developers actually grow their deployment needs
- Reference files can be added for new platforms without changing SKILL.md
- Docker Compose patterns transfer to self-hosted PaaS (Coolify uses Compose) and inform cloud configs

**Negative:**
- Kubernetes-first or serverless-first users may feel the skill is not for them initially
- Docker Compose's local-only nature means the skill must explicitly bridge to production targets
