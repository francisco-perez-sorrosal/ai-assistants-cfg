---
id: dec-122
title: Pipeline Dashboard cross-platform scope — macOS-only v1, Linux deferred
status: accepted
category: architectural
date: 2026-05-07
summary: v1 ships macOS-only via launchd; Linux/systemd support and Windows are deferred to v2 with explicit risk acknowledgment and a documented manual-launch fallback.
tags: [dashboard, cross-platform, macos, launchd, linux, deferred]
made_by: agent
agent_type: systems-architect
pipeline_tier: full
affected_files:
  - scripts/praxion-dashboard
  - commands/dashboard.md
affected_reqs: [REQ-01, REQ-12]
---

## Context

Praxion currently has no cross-platform daemon precedent. `phoenix-ctl` is macOS-only (launchd plist). The user base for Praxion has historically been macOS-centric (the maintainer's primary platform). However, the dashboard's value proposition is broader than Phoenix's — it is a general-purpose entry point intended for any human looking at a Praxion project, including Linux developers who may onboard.

The trade-off: building cross-platform from day one (launchd + systemd + plain shell) doubles the lifecycle script's complexity and triples the test surface (macOS, Linux with systemd, Linux without systemd in containers). Meanwhile, **the dashboard works fine when launched manually with `streamlit run`** — only the persistent daemon layer is platform-specific.

## Decision

**v1 ships macOS-only persistent daemon support** (launchd plist), matching `phoenix-ctl`. Linux and Windows users get a documented manual-launch path:

```
cd <project-root>
PRAXION_PROJECT_ROOT=$(pwd) streamlit run ~/.praxion-dashboard/streamlit_app/app.py
```

— functional, just without daemon persistence. The slash command `/dashboard` detects the platform and either invokes `praxion-dashboard start` (macOS) or prints the manual command (other platforms) with a one-line explanation.

Linux/systemd support is **deferred to v2**, conditional on user demand signals (idea-ledger entry, sentinel cross-platform finding, or explicit user request).

## Considered Options

### Option A — Cross-platform v1 (launchd + systemd + Windows scheduled task)

**Pros**: Inclusive from day one; no follow-up needed. **Cons**: 3× test matrix; systemd requires user-level units (`~/.config/systemd/user/`); Windows scheduled tasks have a different mental model entirely; doubles the ctl script's size and risk surface; no Praxion-internal precedent for any of these.

### Option B — macOS-only v1 with documented Linux manual fallback (chosen)

**Pros**: Matches phoenix-ctl precedent; minimal v1 surface; Linux users can still use the dashboard, just without daemon persistence; clear path to v2.

**Cons**: Linux daemon UX is degraded; the maintainer must remember to add Linux support if/when demand surfaces; a Linux user may perceive "macOS-only" as exclusionary.

### Option C — No daemon at all, only manual launch on every platform

**Pros**: Truly cross-platform; simplest. **Cons**: Loses the "always-on" property the dashboard's value depends on; user must restart on every reboot.

## Consequences

**Positive**: v1 ships fast with proven patterns. The manual-launch path keeps Linux users as second-class citizens but not excluded. v2 work scope is well-defined (one new code path for systemd `.service` files).

**Negative**: A Linux power user opening Praxion will see a "macOS-only" message on first `/dashboard`; this is friction. The cross-platform debt is real and should be tracked in tech-debt ledger as `class: drift` once v1 ships.

**Risks accepted**: Linux user friction for the v1→v2 window. Mitigation: idea-ledger entry capturing the deferral so promethean revisits when demand signal surfaces.
