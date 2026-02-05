# Agent Best Practices

Design principles, anti-patterns, and development workflow for building effective agents.

## Contents

- [Design Principles](#design-principles) — single responsibility, naming, prompts, tools, output
- [Anti-Patterns](#anti-patterns) — common mistakes and fixes
- [Development Workflow](#development-workflow) — from generation to monitoring
- [Integration with Other Features](#integration-with-other-features) — skills, commands, hooks

## Design Principles

### 1. Single Responsibility

Each agent should have one clear purpose.

```markdown
# Good: Focused agent
---
name: security-analyzer
description: Security vulnerability scanning only
---

# Bad: Too broad
---
name: code-helper
description: Helps with code quality, security, performance, and documentation
---
```

### 2. Descriptive Names

Names should indicate purpose clearly.

```markdown
# Good names
code-reviewer, security-analyzer, performance-optimizer, test-generator

# Bad names
helper, assistant, agent1, tool
```

### 3. Detailed Prompts

More guidance leads to better performance.

```markdown
# Good: Specific instructions
When invoked:
1. Run git diff to see changes
2. Focus on security issues
3. Check OWASP Top 10
4. Provide severity ratings

# Bad: Vague instructions
Review the code for issues
```

### 4. Appropriate Tool Access

Grant only necessary tools — see common tool sets in `SKILL.md` Quick Reference.

### 5. Output Structure

Define clear output format.

```markdown
# Good: Structured output
Provide findings as:
**Critical**: [Issues requiring immediate fix]
**High**: [Important improvements]
**Medium**: [Suggestions]

# Bad: Unstructured
Tell me what you find
```

## Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| Overly broad agent ("General purpose helper for all tasks") | Focus on a single domain ("Security vulnerability scanner for authentication code") |
| Vague description ("Use when needed") | Specific triggers ("Use proactively after modifying authentication or authorization code") |
| No output format ("Just tell me what's wrong") | Structured output ("Organize findings by severity: Critical/High/Medium with code examples") |
| Kitchen sink agent (all tools, all tasks) | Specialized agent (read-only tools, focused on analysis) |
| Listing all tools individually | Omit to inherit, or restrict to essentials |

## Development Workflow

### 1. Start with Claude Generation

```bash
/agents
# Let Claude generate initial agent, then customize
```

### 2. Customize and Refine

- Test with real scenarios
- Refine prompts based on results
- Add examples and constraints
- Restrict tools if needed

### 3. Version Control

```bash
git add .claude/agents/your-agent.md
git commit -m "Add [agent] for [purpose]"
```

### 4. Team Testing

- Share with team
- Gather feedback
- Iterate on prompts
- Document usage patterns

### 5. Monitor and Improve

- Track when agent is used
- Identify gaps or confusion
- Update prompts as needed
- Add edge cases discovered

## Integration with Other Features

### Agents + Skills

- Skills provide broad capabilities in the main context
- Agents delegate specific workflows to separate context
- Use `skills` field to inject skill content into agents
- Can coexist in same project

### Agents + Slash Commands

- Commands are user-invoked
- Agents are automatic or explicit
- Can reference agents in commands
- Different use cases

### Agents + Hooks

- Define hooks in agent frontmatter for scoped lifecycle control
- Configure project-level hooks via `SubagentStart`/`SubagentStop` events in `settings.json`
- Use `PreToolUse` hooks for conditional tool validation
- Use `PostToolUse` hooks for post-action automation (linting, formatting)
