# Agent Creator Skill

Skill for creating and managing Claude Code agents (subagents) — specialized AI assistants that run in separate context windows to handle specific workflows.

## What This Skill Does

When activated, this skill provides comprehensive guidance for:

- **Creating agents** with proper frontmatter and system prompts
- **Configuring** tool access, model selection, and permission modes
- **Writing effective prompts** with checklists, output formats, and constraints
- **Avoiding common pitfalls** (overly broad agents, vague descriptions, etc.)

## Activation

The skill activates automatically when Claude detects tasks related to:

- Building custom agents or subagents
- Designing agent architectures or workflows
- Implementing agent-based task delegation

You can also trigger it explicitly by asking about creating agents or referencing it by name.

## Skill Contents

| File | Purpose |
|------|---------|
| `SKILL.md` | Concise hub: file structure, field summary, constraints, quick reference |
| `REFERENCE.md` | Detailed field docs, prompt writing guide, prompt template, CLI agents, troubleshooting |
| `BEST-PRACTICES.md` | Design principles, anti-patterns, development workflow |
| `EXAMPLES.md` | Four structurally distinct agent definitions (read-only, edit-capable, hooks, memory) |
| `README.md` | This file — overview and testing guide |

## Current Agents in This Repository

Agents live in `.claude/agents/` and are available to any project that symlinks to this config (via `install.sh`).

No custom agents currently defined. For planning workflows, use the `software-planning` skill instead.

## Testing

### In Claude Code (CLI)

**Test agent creation guidance:**

```bash
# Start a Claude Code session
claude

# Ask to create an agent — the skill should activate automatically
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

### In Claude Desktop

Claude Desktop uses the same agent definitions but discovery works through MCP and the project context.

**Setup:**

1. Ensure `install.sh` has been run to symlink `.claude/` to `~/.claude/`
2. Open Claude Desktop — it picks up agents from `~/.claude/agents/`

**Test scenarios:**

- Ask to "create a new agent for X" — the skill should activate and guide agent creation
- Verify that agents created via Claude Code are available in Claude Desktop (and vice versa) since both read from `~/.claude/agents/`

### Validation Checklist

After creating or modifying agents, verify:

- [ ] YAML frontmatter parses correctly (no tabs, proper `---` delimiters)
- [ ] `name` is lowercase with hyphens
- [ ] `description` is specific and action-oriented
- [ ] `tools` field is either omitted (inherit all) or restricted appropriately
- [ ] System prompt includes: role, steps, checklist, output format, constraints
- [ ] Agent activates when expected (test with matching prompts)
- [ ] Agent does NOT activate for unrelated tasks
