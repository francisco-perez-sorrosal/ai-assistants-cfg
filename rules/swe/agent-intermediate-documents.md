## Agent Intermediate Documents

Agent documents live in two locations based on their lifecycle:

- **`.ai-work/`** — ephemeral pipeline intermediates (deleted after use)
- **`.ai-state/`** — persistent project intelligence (committed to git)

### `.ai-work/` — Ephemeral Pipeline Documents

```
<project-root>/
  .ai-work/
    IDEA_PROPOSAL.md
    RESEARCH_FINDINGS.md
    SYSTEMS_PLAN.md
    IMPLEMENTATION_PLAN.md
    WIP.md
    LEARNINGS.md
```

- Dot-prefixed — hidden by default in file browsers and `ls`
- Flat structure — all documents at directory root, no per-agent subdirectories
- Created on first use — agents create `.ai-work/` when writing their first document

Scope: **exclusively for agent coordination pipeline documents** — the outputs defined in the [software agent usage](software-agents-usage.md) rule.

Not stored here:
- Command scratch files or skill working files
- Project documentation or ADRs
- Build artifacts or tool caches

### `.ai-state/` — Persistent Project Intelligence

```
<project-root>/
  .ai-state/
    PROJECT_INDEX.md
```

- Committed to git — versioned, shareable, accumulates value over time
- Created on first use — agents create `.ai-state/` when writing their first persistent document

`PROJECT_INDEX.md` contains:
- **Inventory** — what artifacts exist (skills, agents, commands, rules) and their purposes
- **Idea Ledger** — ideas implemented, pending, or discarded (with reasons)
- **Future Paths** — directional possibilities for where the project could go (compatible or mutually exclusive)

Agents that update the index: promethean (idea ledger, future paths), any agent that adds or removes artifacts (inventory).

### Document Lifecycle

| Tier | Location | Documents | Lifetime | Cleanup |
|------|----------|-----------|----------|---------|
| Ephemeral | `.ai-work/` | `IDEA_PROPOSAL.md`, `RESEARCH_FINDINGS.md`, `SYSTEMS_PLAN.md` | Single pipeline run | Delete after downstream agent consumes them |
| Session-persistent | `.ai-work/` | `IMPLEMENTATION_PLAN.md`, `WIP.md`, `LEARNINGS.md` | Across sessions | Merge learnings into permanent locations, then delete at feature end |
| Permanent | `.ai-state/` | `PROJECT_INDEX.md` | Project lifetime | Committed to git, updated incrementally |

### Version Control

Never commit `.ai-work/` or its contents — these are drafts and intermediate artifacts:

```
.ai-work/
```

Always commit `.ai-state/` — it contains persistent project intelligence that accumulates value over time.

### Cleanup

Remove the entire directory when pipeline work is complete:

```bash
rm -rf .ai-work/
```

Before deleting, merge any `LEARNINGS.md` content into permanent locations (CLAUDE.md, ADRs, project docs).

### [CUSTOMIZE] Directory Name
<!-- Override the default `.ai-work/` name if this project uses a different convention:
- Alternative name (e.g., `.ai-scratch/`, `.agent-work/`)
- Reason for the override
-->

### [CUSTOMIZE] Additional Document Types
<!-- List project-specific intermediate documents stored in `.ai-work/`:
- Document name, producing agent, and lifecycle tier
- Whether it follows ephemeral or session-persistent cleanup rules
-->

### [CUSTOMIZE] Cleanup Automation
<!-- Define hooks or scripts that automate cleanup:
- Git hooks that warn on accidental staging of `.ai-work/` contents
- Post-merge scripts that clean up completed pipeline artifacts
- CI checks that fail if `.ai-work/` is committed
-->
