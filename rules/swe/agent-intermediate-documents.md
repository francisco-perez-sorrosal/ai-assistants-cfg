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
    VERIFICATION_REPORT.md
    PROGRESS.md
```

`PROGRESS.md` is an append-only log of agent phase-transition signals. Format: `[TIMESTAMP] [AGENT] Phase N/M: [phase-name] -- [summary] #label1 #key=value`

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
    IDEA_LEDGER_*.md
    SENTINEL_REPORT.md
    SENTINEL_LOG.md
```

- Committed to git — versioned, shareable, accumulates value over time
- Created on first use — agents create `.ai-state/` when writing their first persistent document

`IDEA_LEDGER_*.md` are the promethean's timestamped records of ideation outcomes. Each run produces a new file carrying forward all previous entries:
- **Sentinel baseline** — reference to the sentinel report that informed ideation
- **Implemented / Pending / Discarded** — idea tracking with dates and rationale
- **Future Paths** — directional possibilities for where the project could go (compatible or mutually exclusive)

Artifact inventory is not stored here — it is derivable from the filesystem and audited by the sentinel.

`SENTINEL_REPORT.md` is the sentinel's latest audit report (overwritten each run — only the most recent report is kept). `SENTINEL_LOG.md` is an append-only table of sentinel run summaries (timestamp, health grade, finding counts, ecosystem coherence grade) providing historical metric tracking.

Agents that update `.ai-state/`: promethean (idea ledger, future paths), sentinel (report, log).

### Document Lifecycle

| Tier | Location | Documents | Lifetime | Cleanup |
|------|----------|-----------|----------|---------|
| Ephemeral | `.ai-work/` | `IDEA_PROPOSAL.md`, `RESEARCH_FINDINGS.md`, `SYSTEMS_PLAN.md`, `VERIFICATION_REPORT.md`, `PROGRESS.md` | Single pipeline run | Delete after downstream agent consumes them; merge recurring patterns from `VERIFICATION_REPORT.md` into `LEARNINGS.md` first |
| Session-persistent | `.ai-work/` | `IMPLEMENTATION_PLAN.md`, `WIP.md`, `LEARNINGS.md` | Across sessions | Merge learnings into permanent locations, then delete at feature end |
| Permanent | `.ai-state/` | `IDEA_LEDGER_*.md`, `SENTINEL_REPORT.md`, `SENTINEL_LOG.md` | Project lifetime | Committed to git; `SENTINEL_REPORT.md` overwritten each run, `SENTINEL_LOG.md` append-only, `IDEA_LEDGER_*.md` timestamped per run |

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
