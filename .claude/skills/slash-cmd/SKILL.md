---
name: slash-cmd
description: Creating and managing slash commands for Claude Code -- reusable user-invoked prompts with arguments, tool permissions, and dynamic context. Use when creating custom slash commands, debugging command behavior, fixing argument substitution, converting prompts to reusable commands, or organizing commands with namespacing.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
compatibility: Claude Code
---

# Slash Commands

Guide for creating effective, reusable slash commands.

**Satellite files** (loaded on-demand):
- [REFERENCE.md](REFERENCE.md) -- command patterns, full examples, organization strategies

## What Are Slash Commands

**Slash commands** are user-invoked prompts stored as Markdown files that you trigger with `/` prefix during interactive sessions.

- User-initiated (explicitly type `/command`)
- Single `.md` file per command
- Support arguments (`$ARGUMENTS`, `$1`, `$2`) and dynamic substitution
- Can execute bash commands (`!`) and reference files (`@`)
- Project or personal scope

**Invocation**: `/<command-name> [arguments]`

## File Locations

**Project commands** (shared with team):
```
.claude/commands/<command-name>.md
```

**Personal commands** (across all projects):
```
~/.claude/commands/<command-name>.md
```

**Namespacing with subdirectories**:
```
.claude/commands/
├── git/
│   ├── commit.md      → /commit (shows "project:git")
│   └── merge.md       → /merge (shows "project:git")
└── docs/
    └── generate.md    → /generate (shows "project:docs")
```

## Command Structure

```markdown
---
description: Brief description shown in /help
argument-hint: [expected] [arguments]
allowed-tools: [Bash(git:*), Read, Grep]
model: haiku
---

Your command content here
```

## Frontmatter Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `description` | Brief description (shown in `/help`) | "Create a git commit" |
| `allowed-tools` | Limit tools Claude can use | `Bash(git:*), Read, Grep` |
| `argument-hint` | Show expected arguments | `[message]` or `[pr-number] [priority]` |
| `model` | Use specific model (short-form: `haiku`, `sonnet`, `opus`) | `haiku` |
| `disable-model-invocation` | Prevent auto-invocation | `true` |

## Argument Handling

### All Arguments (`$ARGUMENTS`)

Captures all arguments as a single string:

```markdown
---
argument-hint: [issue-details]
description: Fix issue with provided details
---

Fix issue: $ARGUMENTS

Follow our coding standards and write tests.
```

**Usage**: `/fix-issue 123 high-priority database`
**Result**: `$ARGUMENTS` = `"123 high-priority database"`

### Positional Arguments (`$1`, `$2`, etc.)

Access specific arguments by position:

```markdown
---
argument-hint: [pr-number] [priority] [assignee]
description: Review pull request
---

Review PR #$1 with priority $2 and assign to $3.

Focus on:
- Security vulnerabilities
- Performance issues
- Code style violations
```

**Usage**: `/review-pr 456 high alice`
**Result**: `$1="456"`, `$2="high"`, `$3="alice"`

## Advanced Features

### Bash Command Execution

Use `!` prefix to execute bash commands before the command runs:

```markdown
---
allowed-tools: Bash(git:*), Bash(find:*)
---

## Current Status

!`git status`

## Recent Changes

!`git log --oneline -5`

## Modified Files

!`git diff --name-only`

Review the above changes and create a commit message.
```

### File References

Use `@` prefix to include file contents:

```markdown
---
allowed-tools: Read
---

Review @src/components/Button.tsx for accessibility issues.

Compare:
- Old: @src/old-version.js
- New: @src/new-version.js

Provide a summary of changes.
```

## Slash Commands vs Skills

| Aspect | Slash Commands | Skills |
|--------|---|---|
| **Complexity** | Simple prompts | Complex workflows |
| **Files** | Single `.md` | Multiple files + scripts |
| **Discovery** | Manual (`/command`) | Automatic (context-based) |
| **Scope** | Project or personal | Project or personal |
| **Use case** | Frequently used prompts | Team workflows, expertise |

**Slash commands** -- quick templates, frequently-used instructions, simple operations, reminders.
**Skills** -- multi-file capabilities, complex workflows, team standardization, reference material.

## Best Practices

- **Clear descriptions**: Be specific -- "Review code for security vulnerabilities" not "Helps with code"
- **Always declare `allowed-tools`**: Without it, Claude prompts for permission every time
- **Use `argument-hint`**: Show users what arguments are expected
- **Provide context via `!` commands**: Include git status, project structure, recent changes
- **Test with various inputs**: no arguments, one argument, multiple, special characters

## Common Mistakes

- **Missing descriptions** -- commands without `description` are invisible in `/help`
- **No tool restrictions** -- without `allowed-tools`, Claude prompts every time
- **Name conflicts** -- project commands override personal ones with the same name; use subdirectories
- **Overloaded commands** -- slash commands work best for focused tasks; use Skills for complex workflows
- **Untested arguments** -- `$ARGUMENTS` might be empty; test and handle missing values gracefully

## Permission Management

Allow Claude to auto-invoke commands:

```bash
/permissions
# Allow: SlashCommand:/my-command:*
```

Prevent auto-invocation for specific commands:

```markdown
---
disable-model-invocation: true
---
```

## Debugging

```bash
# List all commands
ls -R .claude/commands/
ls -R ~/.claude/commands/

# View command content
cat .claude/commands/my-command.md
```

Within Claude Code, the `Read` and `Glob` tools can also inspect command files directly.

Verify: proper `---` delimiters, valid YAML, correct field names, expected argument substitution.

## Creation Workflow

1. **Define** -- identify the repeated prompt or workflow to automate
2. **Create** -- write the `.md` file with frontmatter and content
3. **Test** -- invoke with `/command` and verify behavior with various inputs
4. **Iterate** -- refine based on output; adjust tools, arguments, context
5. **Share** -- commit to `.claude/commands/` for team use

## Related Skills

- [`agent-skills`](../agent-skills/SKILL.md) -- the spec for creating skills; when a command outgrows a single file, convert it to a skill
- [`agent-creator`](../agent-creator/SKILL.md) -- for building custom agents; helps distinguish when to use a command vs an agent

## Resources

- [Official Documentation](https://docs.anthropic.com/en/docs/claude-code/slash-commands)
- Extended examples: See [REFERENCE.md](REFERENCE.md) for command patterns and organization strategies
