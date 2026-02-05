---
name: agent-creator
description: Guides creation of Claude Code agents (subagents) with best practices for prompt writing, tool configuration, and lifecycle management. Use when building custom agents, designing agent workflows, spawning subagents, delegating tasks to agents, or using the /agents command.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# Agent Creator

Guide for building agents — specialized subprocesses with separate context windows, independent tool permissions, and focused system prompts.

**Satellite files** (loaded on-demand):

- `REFERENCE.md` — detailed field docs, prompt writing guide, prompt template, CLI agents, troubleshooting
- `BEST-PRACTICES.md` — design principles, anti-patterns, development workflow
- `EXAMPLES.md` — complete agent definitions showing distinct patterns (read-only, edit-capable, hooks, memory)

## Creating Agents

**Quick**: Run `/agents` for guided creation (recommended starting point).

**Manual**: Create a markdown file in `.claude/agents/` (project) or `~/.claude/agents/` (personal).

### Agent File Structure

```markdown
---
name: agent-name
description: When this agent should be invoked
tools: tool1, tool2, tool3  # Optional: omit to inherit all
disallowedTools: tool4      # Optional: denylist
model: sonnet               # Optional: sonnet/opus/haiku/inherit (default: inherit)
permissionMode: default     # Optional: default/acceptEdits/dontAsk/bypassPermissions/plan
color: blue                 # Optional: UI background color
skills: skill1, skill2      # Optional: inject skill content at startup
hooks:                       # Optional: lifecycle hooks scoped to this agent
memory: user                 # Optional: persistent memory (user/project/local)
---

Your agent's system prompt goes here.
Define role, expertise, instructions, constraints, and output format.
```

### Configuration Fields Summary

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier, lowercase with hyphens |
| `description` | Yes | When Claude should delegate — be specific, include "use proactively" for auto-invocation |
| `tools` | No | Allowlist of tools; omit to inherit all |
| `disallowedTools` | No | Denylist; removed from inherited/specified set |
| `model` | No | `inherit` (default), `sonnet`, `opus`, `haiku` |
| `permissionMode` | No | `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan` |
| `color` | No | UI background color for identification |
| `skills` | No | Skills injected into context (not inherited from parent) |
| `hooks` | No | `PreToolUse`, `PostToolUse`, `Stop` events |
| `memory` | No | Cross-session learning: `user`, `project`, `local` |

For detailed field documentation, examples, and the prompt template, see `REFERENCE.md`.

## Agent Example

A concise debugger agent showing the key structural elements:

```markdown
---
name: debugger
description: Debugging specialist for errors and test failures. Use proactively when encountering any issues.
tools: Read, Edit, Bash, Grep, Glob
---

You are an expert debugger specializing in root cause analysis.

When invoked:
1. Capture error message and stack trace
2. Identify reproduction steps
3. Isolate the failure location
4. Implement minimal fix
5. Verify solution works

For each issue, provide:
- Root cause explanation
- Evidence supporting the diagnosis
- Specific code fix
- Prevention recommendations

Focus on fixing the underlying issue, not the symptoms.
```

For more complete examples, see `EXAMPLES.md`.

## Agent Location Hierarchy

Higher priority wins when names collide:

| Priority | Location | Scope |
|----------|----------|-------|
| 1 (Highest) | `--agents` CLI flag | Current session only |
| 2 | `.claude/agents/` | Current project |
| 3 | `~/.claude/agents/` | All projects |
| 4 (Lowest) | Plugin `agents/` | Where plugin is enabled |

**Best practice**: Use project-level agents (`.claude/agents/`) for team collaboration. For CLI-defined ephemeral agents, see `REFERENCE.md`.

## Constraints and Runtime Behavior

- **Subagents cannot spawn subagents.** Do not include `Task` in tools. Chain agents from the main conversation instead.
- **System prompt isolation.** Agents receive only their markdown body + basic env details, not the full Claude Code system prompt.
- **Session loading.** Agents load at session start. Manually added files need a restart or `/agents`.
- **Foreground**: Blocks main conversation; permission prompts pass through.
- **Background**: Runs concurrently; permissions pre-approved; press **Ctrl+B** to background a running agent.
- **Disabling agents**: `claude --disallowedTools "Task(my-agent)"` or add to `deny` array in settings.
- **Transcripts** persist at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`.

## Deployment Checklist

- [ ] Single, clear responsibility
- [ ] Descriptive name matching purpose
- [ ] Specific description with trigger words
- [ ] Detailed system prompt with steps, checklist, output format, constraints
- [ ] Appropriate tools granted (or inherited)
- [ ] Correct model selected
- [ ] Tested with real scenarios
- [ ] Version controlled in git

## Quick Reference

### Minimal Template

```markdown
---
name: agent-name
description: Specific description of when to use this agent
---

You are [role] specializing in [domain].

When invoked:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Checklist:
- [Item 1]
- [Item 2]

Output format:
[How to structure output]

Constraints:
- [Constraint 1]
- [Constraint 2]
```

### Common Tool Sets

```yaml
# Read-only
tools: Read, Grep, Glob, Bash

# Development
tools: Read, Edit, Grep, Glob, Bash, Write

# Full access — omit tools field
```
