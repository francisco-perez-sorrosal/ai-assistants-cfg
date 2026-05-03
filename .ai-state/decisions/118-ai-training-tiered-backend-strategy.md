---
id: dec-118
title: Neo-cloud abstraction uses tiered backend strategy (local default + SkyPilot default-remote + opt-in direct adapters)
status: proposed
category: architectural
date: 2026-05-03
summary: Praxion ships a generic training_job_descriptor with three backend tiers — local subprocess (modes A/B), SkyPilot for default-remote (mode C; covers 20+ providers), and opt-in direct adapters when users commit to a provider (RunPod via @runpod/mcp-server is the v1 reference).
tags: [ml-training, neo-cloud, abstraction, deployment, skypilot, runpod, archetype-extension]
made_by: agent
agent_type: systems-architect
pipeline_tier: standard
affected_files:
  - skills/neo-cloud-abstraction/SKILL.md
  - skills/neo-cloud-abstraction/references/local-backend.md
  - skills/neo-cloud-abstraction/references/skypilot-backend.md
  - skills/neo-cloud-abstraction/references/runpod-direct-adapter.md
  - skills/deployment/SKILL.md
  - skills/deployment/references/ai-native-platforms.md
  - commands/run-experiment.md
  - .ai-state/SYSTEM_DEPLOYMENT.md
affected_reqs: []
---

# ADR — Tiered backend strategy for the neo-cloud abstraction

## Context

Praxion-managed ML projects span a local-to-remote infrastructure continuum: an experimenter on a Mac M-series, on a rented H100 box (SSH'd in), or on a laptop dispatching to a remote GPU. Three operational modes (A: co-located on owned GPU; B: co-located on rented GPU; C: separated) define this surface.

Two failure modes bound the design space:

- **Adopting SkyPilot as the universal abstraction** locks every Praxion-managed ML project into one orchestration tool, contrary to Praxion's "assistant-agnostic shared assets" design principle and creates a single point of dependency.
- **Per-provider direct adapters only (no shared default)** means Praxion ships with zero remote-provider coverage on day 1; every user has to build per-provider plumbing before running their first remote experiment, which is bad ergonomics for a meta-project.

The `RESEARCH_FINDINGS.md` "Theme 3 — SkyPilot is the default remote backend, not the meta-layer" frames the resolution: a tiered strategy that gives day-1 coverage without lock-in.

Versions verified 2026-05-03 (per `external-api-docs` skill — chub had no entry for SkyPilot or RunPod MCP, so versions were verified against PyPI and npm directly):

- **SkyPilot 0.12.1** (PyPI) — March 2026 release shipped Agent Skill for Claude Code; supports 20+ providers including RunPod, Lambda, Crusoe, CoreWeave, Modal
- **`@runpod/mcp-server` 1.1.0** (npm) — official MCP server covering pods, serverless, volumes, registries

## Decision

**Three-tier backend model under a Praxion-native generic abstraction:**

| Tier | Backend | Serves operational modes | When | Ships in v1 |
|---|---|---|---|---|
| **Default — local** | Direct process invocation (`subprocess.run` semantics) | A and B (co-located, owned or rented GPU) | autoresearch on Mac M-series, RTX, on-prem GPUs, rented GPU boxes where Praxion is installed locally | Yes — ~0 LOC |
| **Default — remote** | SkyPilot 0.12.1 | C (Praxion separated) | Any remote provider; exploration; multi-cloud workflows; the day-1 path without commitment | Yes — one SkyPilot adapter |
| **Specialization — direct adapter** | `@runpod/mcp-server` 1.1.0 (v1 reference) | C, when committed to RunPod | Native MCP integration; lower latency; escape SkyPilot indirection | Yes — reference recipe in skill |
| Specialization (v2) | Lambda direct (REST), Crusoe direct (REST), CoreWeave direct (K8s) | C, when committed | Per-provider native; v2 candidates | No — deferred |

The abstraction's contract — `training_job_descriptor` schema and 8 lifecycle operations — is invariant. Only the backend implementation changes per tier. The descriptor does not contain a `mode:` or `backend:` field; mode is a project-level configuration in `.ai-state/neo_cloud_backend.yaml`.

The artifact shape for direct adapters is **a skill reference + integration recipe** rather than a new MCP server authored by Praxion. RunPod already ships `@runpod/mcp-server`; Praxion's contribution is the configuration pattern and the recipe, not duplicate infrastructure. Same shape applies to v2 specializations.

## Considered Options

### Option 1 — SkyPilot as the meta-layer (universal)

**Pros:**
- One adapter covers 20+ providers
- SkyPilot's YAML is a real abstraction; we could adopt it
- Ships with multi-cloud failover, spot recovery, cost optimization

**Cons:**
- Locks every Praxion ML project into SkyPilot dependency
- Local execution still needs a separate path (SkyPilot is fundamentally remote-only)
- Conflicts with Praxion's "assistant-agnostic shared assets" principle
- A user committed to RunPod gains nothing from SkyPilot's overhead

### Option 2 — Per-provider direct adapters only (no SkyPilot)

**Pros:**
- Native integration per provider; no extra dependency
- Maximum flexibility per provider's specific features
- Simplest at the per-adapter level

**Cons:**
- Day-1 coverage is whatever adapters ship initially (RunPod only — single-vendor)
- Each new provider is a Praxion-side adapter project before users can use them
- "Try a few providers, see what fits" workflow requires building all of them upfront
- Bad ergonomics for a management layer

### Option 3 — Tiered (chosen)

**Pros:**
- Day-1 broad coverage via SkyPilot default-remote (20+ providers)
- No lock-in; SkyPilot is the *default*, not a *requirement*
- Local default at ~0 LOC covers the common autoresearch case (Mac M2, rented H100 box)
- Direct adapters are *opt-in* — users only build them after committing to a provider
- Exploration → commitment is a first-class user journey
- Consistent with `skills/deployment/SKILL.md` pattern (Docker / PaaS / K8s / AI-native are *reference patterns*, not mandates)
- The descriptor is mode-invariant (modes A/B/C share one schema)

**Cons:**
- Skill complexity: three backends to document instead of one
- SkyPilot version pin in skill content requires periodic refresh
- Per-provider MCPs may obsolete the direct-adapter path within 12 months (acceptable — abstraction protects the user from this)

## Consequences

**Positive:**
- Praxion does not invent infrastructure; it teaches *which* infrastructure to use *when* and provides an invariant contract
- The exploration → commitment lifecycle is supported natively
- The local backend's "no-op or trivially-implementable" lifecycle ops (e.g., `pricing_query` returns `0.0`) prove the abstraction's correctness — a leaking abstraction would force the descriptor to know its mode
- v2 direct adapters (Lambda/Crusoe/CoreWeave) follow the same opt-in pattern; the work is bounded

**Negative:**
- Three backend recipes in the `neo-cloud-abstraction` skill instead of one
- SkyPilot version drift risk (R1 in SYSTEMS_PLAN); mitigated by sentinel staleness check on the skill
- Single-vendor direct adapter (RunPod) for v1 reference; mitigated by v2 plan adding three more

**Neutral:**
- The `training_job_descriptor` schema is YAML; it is fixed in this ADR but can evolve via additive-only changes (new optional fields are non-breaking)
- The 8 lifecycle operations are protocol-level; new operations require an ADR; existing ones are stable

## API version and capability verification

Per the cross-agent skill conventions rule, library version checks are mandatory before naming libraries in an ADR.

- **SkyPilot 0.12.1**: confirmed via `pip index versions skypilot` 2026-05-03. Supports RunPod, Lambda, Crusoe, CoreWeave, Modal, GCP, AWS, Azure, Kubernetes, Vast.ai. Spot recovery, multi-cloud failover, managed spot jobs all confirmed in research. Capability fit: confirmed.
- **`@runpod/mcp-server` 1.1.0**: confirmed via `npm view @runpod/mcp-server version` 2026-05-03. Covers pod create/list/start/stop, serverless endpoints, network volumes, container registries. Capability fit: confirmed.

Both pinned versions are noted in the `neo-cloud-abstraction` skill body as the v1 baseline; future skill updates revisit at minor-version refreshes.
