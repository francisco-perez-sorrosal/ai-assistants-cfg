## Agent Intermediate Documents

Agent pipeline documents (`RESEARCH_FINDINGS.md`, `SYSTEMS_PLAN.md`, `IMPLEMENTATION_PLAN.md`, `WIP.md`, `LEARNINGS.md`) live in a dedicated `.ai-work/` directory at the project root — not scattered across the root itself.

### Location

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

### Scope

This directory is **exclusively for agent coordination pipeline documents** — the outputs defined in the [software agent usage](software-agents-usage.md) rule.

Not stored here:
- Command scratch files or skill working files
- Project documentation or ADRs
- Build artifacts or tool caches

### Document Lifecycle

| Tier | Documents | Lifetime | Cleanup |
|------|-----------|----------|---------|
| Ephemeral | `IDEA_PROPOSAL.md`, `RESEARCH_FINDINGS.md`, `SYSTEMS_PLAN.md` | Single pipeline run | Delete after downstream agent consumes them |
| Session-persistent | `IMPLEMENTATION_PLAN.md`, `WIP.md`, `LEARNINGS.md` | Across sessions | Merge learnings into permanent locations, then delete at feature end |

### Version Control

Never commit `.ai-work/` or its contents. These are drafts and intermediate artifacts. Add a single gitignore entry:

```
.ai-work/
```

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
