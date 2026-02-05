---
name: Claude Agents
description: Creating effective Claude Code agents (subagents) with best practices for delegation, specialized workflows, and team collaboration. Use when building custom agents, designing agent architectures, or implementing agent-based workflows.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# Creating Effective Claude Agents

Guide for building specialized agents that handle specific workflows with separate context windows.

**Satellite files** (loaded on-demand):

- `REFERENCE.md` — detailed field docs, prompt writing guide, prompt template, troubleshooting
- `BEST-PRACTICES.md` — design principles, anti-patterns, development workflow, integrations
- `EXAMPLES.md` — complete agent definitions (code-reviewer, security-analyzer, debugger, db-reader with hooks, etc.)

## When to Use Agents

| Feature | Agents | Skills | Slash Commands |
|---------|--------|--------|----------------|
| Separate context | Yes | No | No |
| Complex workflows | Yes | Yes | No |
| Automatic invocation | Yes | Yes | No |
| User-triggered | Optional | No | Yes |
| Tool restrictions | Yes | Yes | Possible |

**Use agents** for specialized workflows needing separate context, independent tool permissions, or context preservation. **Use skills** when same-context knowledge is sufficient. **Use slash commands** for simple, frequently used prompts.

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

**Best practice**: Use project-level agents (`.claude/agents/`) for team collaboration.

**CLI-defined agents** (session-only, not saved to disk):

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer. Use proactively after code changes.",
    "prompt": "You are a senior code reviewer...",
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "model": "sonnet"
  }
}'
```

## Using Agents

**Automatic**: Claude delegates based on task description, agent `description` field, and context. Include "use proactively" or "MUST BE USED" in descriptions to encourage auto-delegation.

**Explicit**: `Use the code-reviewer agent to check my recent changes`

**Resume**: `Continue that code review` — resumed agents retain full conversation history.

## Common Patterns

| Pattern | Tools | Permission Mode |
|---------|-------|-----------------|
| Research and Report | Read, Grep, Glob, Bash | `plan` |
| Analyze and Fix | Read, Edit, Grep, Glob, Bash | `default` |
| Validate and Approve | Read, Grep, Glob, Bash | `default` |
| Chain Agents | Varies | Varies |

Chain example: `Use code-reviewer to identify issues, then test-generator to add tests`

## Model Selection

| Model | Best For |
|-------|----------|
| **inherit** (default) | General-purpose agents, session consistency |
| **sonnet** | Most agents — balanced capability and speed |
| **opus** | Complex reasoning, architectural analysis |
| **haiku** | Quick searches, simple analysis, high-volume operations |

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
