---
description: Onboard the current project to work with the Praxion plugin ecosystem
allowed-tools: [Bash(git:*), Bash(grep:*), Read, Write, Edit, Glob, Grep, AskUserQuestion]
---

Onboard the current project directory to work cleanly with the Praxion plugin (i-am). Run checks and apply fixes for `.gitignore` hygiene, plugin installation, and project-level configuration.

## Pre-flight

1. Confirm the working directory is a git repository (`git rev-parse --git-dir`). If not, stop: "This command must be run inside a git repository."
2. Detect the project root (`git rev-parse --show-toplevel`) and work relative to it for all checks

## Checks

Run all checks, collect results, then present a summary before making changes. Group into **needs action** and **looks good**.

### 1. `.gitignore` hygiene

Check that the project's root `.gitignore` contains these entries:

- `.ai-work/` -- ephemeral pipeline intermediates (must not be committed)

If `.gitignore` does not exist, create it with the required entries. If it exists but entries are missing, append them under an `# AI assistants` comment block. Do not duplicate entries already present.

### 2. `.ai-state/` not excluded

`.ai-state/` is persistent project intelligence and SHOULD be committed. Check whether `.gitignore` contains `.ai-state/` or `.ai-state`. If found, flag it as a warning: ".ai-state/ is excluded from git but should be committed -- it contains persistent project intelligence (idea ledgers, sentinel reports)." Ask the user whether to remove the exclusion entry.

### 3. Plugin installation

Check whether the i-am plugin is installed by looking for `i-am@bit-agora` in `~/.claude/plugins/installed_plugins.json`:

- If the file does not exist or does not contain `i-am@bit-agora`, warn: "The i-am plugin is not installed. Run install.sh from the Praxion repo to install it."
- If installed, report the version and install path from the JSON entry

### 4. Project CLAUDE.md

Check whether a `CLAUDE.md` file exists at the project root.

- If missing, suggest: "No project-level CLAUDE.md found. Run `claude init` to generate one from the codebase." Do not create it directly -- `claude init` analyzes the project and produces better results.
- After `claude init` completes (or if `CLAUDE.md` already exists), append the following block if not already present (check for the `## Agent Pipeline` heading to detect prior onboarding):

```markdown
## Agent Pipeline

Follow the Understand, Plan, Verify methodology. For multi-step work (Standard/Full tier), delegate to specialized agents in pipeline order. Each pipeline operates in an ephemeral `.ai-work/<task-slug>/` directory (deleted after use); permanent artifacts go to `.ai-state/` (committed to git).

1. **researcher** → `.ai-work/<slug>/RESEARCH_FINDINGS.md` — codebase exploration, external docs
2. **systems-architect** → `.ai-work/<slug>/SYSTEMS_PLAN.md` + ADR drafts under `.ai-state/decisions/drafts/` (promoted to stable `<NNN>-<slug>.md` at merge-to-main by `scripts/finalize_adrs.py`) + `.ai-state/ARCHITECTURE.md` (architect-facing) + `docs/architecture.md` (developer-facing)
3. **implementation-planner** → `.ai-work/<slug>/IMPLEMENTATION_PLAN.md` + `WIP.md` — step decomposition
4. **implementer** + **test-engineer** (concurrent) → code + tests — execute steps from the plan
5. **verifier** → `.ai-work/<slug>/VERIFICATION_REPORT.md` — post-implementation review

**Independent audits**: the `sentinel` agent runs outside the pipeline and writes timestamped `.ai-state/SENTINEL_REPORT_*.md` plus an append-only `.ai-state/SENTINEL_LOG.md`. Trigger it for ecosystem health baselines (before first ideation, after major refactors).

**From PoC to production**: the feature pipeline is one milestone of many. The full journey runs through sentinel audit → CI/CD (`cicd-engineer`) → deployment (`deployment` skill) → first release (`/release`) → persistent decisions as ADRs → cross-session memory (`memory.json` + `observations.jsonl`). See the milestone table at `docs/getting-started.md#journey-poc-to-production`.

Always include expected deliverables when delegating to an agent. The agent coordination protocol rule has full delegation checklists.
```

### 5. Existing `.ai-work/` leftovers

Check if `.ai-work/` exists with content from a previous session. If found, note: ".ai-work/ contains leftover pipeline files. Run /clean-work to clean up when ready."

## Apply Changes

After presenting the summary:

1. Ask the user to confirm before making any changes
2. Apply `.gitignore` fixes (if needed)
3. Apply `.ai-state/` exclusion removal (if user approved)
4. Create `CLAUDE.md` (if user approved)
5. Stage and commit only the files this command changed, with message: `chore: Onboard project for Praxion plugin`
6. Print final summary of what was done
