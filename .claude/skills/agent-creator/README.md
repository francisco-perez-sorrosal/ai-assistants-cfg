# Agent Creator Skill

Skill for creating and managing Claude Code agents (subagents) -- specialized AI assistants that run in separate context windows to handle specific workflows.

## What This Skill Does

When activated, this skill provides guidance for:

- **Creating agents** with proper frontmatter and system prompts
- **Configuring** tool access, model selection, and permission modes
- **Writing effective prompts** with checklists, output formats, and constraints
- **Integrating** agents with skills, slash commands, and lifecycle hooks

## Activation

The skill activates automatically when Claude detects tasks related to:

- Building custom agents or subagents
- Designing agent architectures or workflows
- Implementing agent-based task delegation
- Using the Task tool or defining subagent_type

You can also trigger it explicitly by asking about creating agents or referencing it by name.

## Skill Contents

| File | Purpose |
|------|---------|
| `SKILL.md` | Hub: file structure, field summary, example, anti-patterns, integration, checklist |
| `references/configuration.md` | Detailed field docs, prompt writing guide, prompt template, CLI agents, troubleshooting |
| `references/examples.md` | Four structurally distinct agent definitions (read-only, edit-capable, hooks, memory) |
| `README.md` | This file -- overview and testing guide |

## Current Agents in This Repository

Agents live in `.claude/agents/` and are available to any project that symlinks to this config (via `install.sh`).

No custom agents currently defined. For planning workflows, use the `software-planning` skill instead.

## Related Skills

- [`agent-skills`](../agent-skills/SKILL.md) -- the spec for creating skills that agents can consume via the `skills` field
- [`slash-cmd`](../slash-cmd/SKILL.md) -- for understanding the distinction between slash commands and agents

## Testing

### In Claude Code (CLI)

**Test agent creation guidance:**

```bash
# Start a Claude Code session
claude

# Ask to create an agent -- the skill should activate automatically
> I want to create an agent for reviewing documentation quality

# Or reference it explicitly
> Using the agent-creator skill, help me build a linter agent
```

**Test an existing agent:**

```bash
# Invoke an agent explicitly
> Use the code-reviewer agent to check this PR

# Or trigger it via matching context
> Review the security implications of this change
```

**Verify agent discovery:**

```bash
# List available agents via the /agents command
/agents
```

**Test agent file creation:**

```bash
# Ask Claude to create an agent file and verify it lands in .claude/agents/
> Create a code-reviewer agent for this project

# Then check the result
ls -la .claude/agents/
cat .claude/agents/code-reviewer.md
```

### Validation Checklist

After creating or modifying agents, verify:

- [ ] YAML frontmatter parses correctly (no tabs, proper `---` delimiters)
- [ ] `name` is lowercase with hyphens
- [ ] `description` is specific and action-oriented
- [ ] `tools` field is either omitted (inherit all) or restricted appropriately
- [ ] System prompt includes: role, steps, checklist, output format, constraints
- [ ] Agent activates when expected (test with matching prompts)
- [ ] Agent does NOT activate for unrelated tasks
