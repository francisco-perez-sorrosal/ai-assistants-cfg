---
id: dec-200
title: Harden Obsidian Shape B link safety — pin .obsidian/app.json link config and deny move/rename
status: accepted
category: behavioral
date: 2026-05-20
summary: Pin useMarkdownLinks:true + alwaysUpdateLinks:false in .obsidian/app.json (Phase 8d.4) and add Bash(obsidian move*)/rename* to the permissions.deny set (Phase 8d.5b, whose predicate becomes a subset-presence check for idempotent upgrade), so a repo-as-vault cannot let Obsidian tooling rewrite project-artifact links into wikilink form or auto-rewrite link bodies on rename. Supersedes the dec-196 allowlist (move/rename move from allowed to denied for link integrity); re-affirms dec-198 (Shape B retained and hardened rather than reversed).
tags: [obsidian, shape-b, link-safety, allowlist, settings-json, onboarding]
made_by: user
supersedes: dec-196
re_affirms: dec-198
affected_files:
  - claude/canonical-blocks/obsidian-integration.md
  - commands/onboard-project.md
  - commands/new-project.md
  - docs/obsidian-integration.md
  - .obsidian/app.json
  - .claude/settings.json
---

## Context

Praxion's Obsidian integration (Shape B, dec-198) registers a project repository as an Obsidian vault. Once a git repo doubles as a vault, Obsidian's default link behavior can corrupt the link forms project artifacts depend on — standard Markdown `[text](path)` links and ADR id cross-references — through two write-path behaviors:

1. **New-link format.** Obsidian's default is `useMarkdownLinks: false`, so any link it authors (via the app, `template:insert`, etc.) is a `[[wikilink]]` — a form Praxion's docs do not use and its cross-reference validators (doc-engineer, sentinel) do not resolve.
2. **Auto link-rewrite on rename.** With "Automatically update internal links" enabled, renaming or moving a file makes Obsidian rewrite link bodies across other files. The CLI exposes this through the `move` and `rename` subcommands, which dec-196 placed on the agent allowlist.

Registering the repository as a vault is otherwise passive — Obsidian does not modify files merely by having the folder in its registry. The risk is confined to the write path: link authoring and rename/move. The user raised the concern that repo-as-vault would "screw the links of project artifacts" in Praxion and in every onboarded project (Shape B is default-on). Reversing Shape B was considered and rejected: the navigation/backlink value is real, and the link risk is fully addressable by constraining the write path.

## Decision

Keep Shape B and harden it. Close both write-path vectors, on two enforcement layers, shipped through the existing Phase 8d onboarding sub-flow so every managed project (and Praxion's own dogfood state) inherits the protection:

- **Phase 8d.4 — `.obsidian/app.json` link config.** Pin `useMarkdownLinks: true` and `alwaysUpdateLinks: false`, merged non-destructively into any existing `app.json` (create `.obsidian/` and `app.json` if absent). `app.json` is committed (the 8d.1 `.gitignore` block ignores workspace/cache/appearance/hotkeys, not `app.json`), so the safe defaults travel with every clone. The predicate skips only when both keys already hold the safe values. This replaces the prior 8d.4 no-op.
- **Phase 8d.5b — deny `move`/`rename`.** Add `Bash(obsidian move*)` and `Bash(obsidian rename*)` to the `permissions.deny` set (now ten entries). File renames go through `git mv`, so git tracks the rename and no link bodies are silently rewritten. This is a backstop independent of `app.json` — a clone whose `app.json` was altered is still protected at the tool-permission layer. The 8d.5b predicate changes from "is the `eval` entry present?" to a subset-presence check (`($req - deny) | length == 0`), so re-running `/onboard-project` on a project onboarded under the older eight-entry set adds the missing entries instead of skipping.

The denial of `move`/`rename` is for **link integrity**, not security — distinct from the eight security denials (`eval`, plugin lifecycle, theme lifecycle, `delete --permanent`). The canonical block, both onboarding commands, and `docs/obsidian-integration.md` carry the rationale.

## Considered Options

### Option 1 — Harden Shape B (chosen)

- **Pros:** Preserves the vault-navigation/backlink value of dec-198. Closes both link vectors structurally (config pin + tool-permission deny). Ships to all onboards through the existing Phase 8d sub-flow with no new phase. Fills the gap the original 8d.4 left open (it was a deferred no-op for `.obsidian/` starter config). The `app.json` write is narrow (two keys, non-destructive), honoring the original deferral concern that broad starter config could conflict with a user's vault.
- **Cons:** Adds a fourth Phase 8d surface and two deny entries. `move`/`rename` are no longer available through the CLI; agents reorganize via `git mv` (correct for a git repo regardless).

### Option 2 — Reverse Shape B entirely

- **Pros:** No project repo ever becomes a vault; the concern disappears by construction.
- **Cons:** Throws away the navigation/backlink/search tooling for a problem confined to the write path. Largest blast radius (supersede dec-198, edit both onboarding commands, the canonical block, docs, and un-register vaults). Rejected — disproportionate to a vector that two narrow guardrails close.

### Option 3 — `app.json` pin only, leave `move`/`rename` allowed

- **Pros:** Smallest change; `alwaysUpdateLinks: false` alone stops auto-rewrite on rename.
- **Cons:** Single layer — a clone whose `app.json` was changed (or never written) loses the protection. `obsidian rename` also hides renames from git even when it does not rewrite other files. The deny is a cheap, config-independent backstop. Rejected in favor of defense in depth.

### Option 4 — Prose-only guidance ("agents should not author wikilinks / use git mv")

- **Pros:** Zero enforcement surface.
- **Cons:** Prose-only policies fail silently — the same reasoning dec-196 used to reject prose-only allowlist enforcement. Rejected.

## Consequences

**Positive:**

- Vault tooling can no longer rewrite project-artifact links into wikilink form, and Obsidian no longer auto-rewrites link bodies on rename — closed by config and by tool-permission deny.
- The protection ships to every onboarded project and to Praxion's own state via the existing Phase 8d sub-flow; no agent-pipeline changes.
- The 8d.5b subset-presence predicate makes the deny set upgrade-idempotent — re-running `/onboard-project` retrofits already-onboarded projects with the new entries.
- The two-layer design (config + deny) is defense in depth: each layer is independently sufficient for its vector, and the deny survives a config change.

**Negative:**

- Phase 8d gains a fourth surface (`app.json`) and the deny set grows to ten entries — slightly more onboarding surface and a second link-safety touchpoint to keep aligned with the canonical block.
- `obsidian move`/`rename` are unavailable to agents; vault-note reorganization goes through `git mv`. Acceptable: the repo is git-first, vault-second.
- A clone opened in Obsidian where the user manually re-enables wikilinks/auto-update could still author non-conforming links — the deny on `move`/`rename` mitigates the rename vector, but the new-link vector relies on the committed `app.json` not being overridden by the user.

## Prior Decision

This ADR **supersedes dec-196** (Obsidian CLI agent allowlist): `move` and `rename` move from the allowed set to the denied set, and a fourth enforcement surface (`.obsidian/app.json`) is added to the policy. The security denials and the two-layer (settings.json mechanical + CLAUDE.md prose) enforcement model of dec-196 are retained unchanged.

This ADR **re-affirms dec-198** (Shape B default-on): reversing repo-as-vault was explicitly considered in response to the link-corruption concern and rejected. dec-198 still holds — the integration's value is real and the link risk is confined to the write path, which this decision constrains. The evidence that would justify a future supersession of dec-198 is a demonstrated link-corruption incident that these two guardrails fail to prevent (e.g., a vault write path other than authoring/rename that mutates link bodies), or the navigation/backlink value proving unused in practice.
