---
name: Claude Slash Commands
description: Creating effective Claude Code slash commands with proper syntax, arguments, frontmatter, and best practices. Use when creating custom slash commands, debugging command behavior, or converting prompts to reusable commands.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# Claude Slash Commands

Guide for creating effective, reusable slash commands in Claude Code.

## What Are Slash Commands

**Slash commands** are user-invoked prompts stored as Markdown files that you trigger with `/` prefix during interactive sessions.

**Key characteristics**:
- User-initiated (explicitly type `/command`)
- Simple to create (single `.md` file)
- Support arguments and dynamic substitution
- Can execute bash commands and reference files
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

### Basic Command

```markdown
Your command content here
```

### With Frontmatter

```markdown
---
description: Brief description shown in /help
argument-hint: [expected] [arguments]
allowed-tools: [Bash(git:*), Read, Grep]
model: claude-3-5-haiku-20241022
---

Your command content here
```

## Frontmatter Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `description` | Brief description (shown in `/help`) | "Create a git commit" |
| `allowed-tools` | Limit tools Claude can use | `Bash(git:*), Read, Grep` |
| `argument-hint` | Show expected arguments | `[message]` or `[pr-number] [priority]` |
| `model` | Use specific model | `claude-3-5-haiku-20241022` |
| `disable-model-invocation` | Prevent auto-invocation | `true` |

## Argument Handling

### Method 1: All Arguments (`$ARGUMENTS`)

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

### Method 2: Positional Arguments (`$1`, `$2`, etc.)

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

**Use positional arguments when**:
- Arguments serve different purposes
- Need to provide defaults for missing arguments
- Want structured, explicit parameter roles

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

## Command Patterns

### Pattern 1: Git Commit

```markdown
---
allowed-tools: [Bash(git add:*), Bash(git status:*), Bash(git commit:*)]
argument-hint: [message]
description: Create git commit with descriptive message
---

## Context

- Status: !`git status`
- Staged: !`git diff --staged`
- Branch: !`git branch --show-current`

## Task

Create commit with message: $ARGUMENTS

Follow conventional commits format:
- type(scope): summary (under 50 chars)
- blank line
- detailed explanation
- reference related issues
```

### Pattern 2: Code Review

```markdown
---
argument-hint: [file-path] [focus-area]
description: Review file focusing on specific area
allowed-tools: [Read, Grep]
---

Review @$1 focusing on $2.

Analyze:
1. Code quality
2. Best practices
3. Security considerations
4. Performance implications

Provide actionable recommendations.
```

### Pattern 3: Project Setup

```markdown
---
argument-hint: [project-name] [optional-tool]
description: Create new project with specified tool
---

Create project named "$1" using ${2:-default-tool}.

Setup:
- Initialize project structure
- Configure dependencies
- Add basic tests
- Create README
```

### Pattern 4: Simple Template

```markdown
---
description: Generate test names for TDD
---

Generate descriptive test names for this scenario:

[User provides scenario after command]
```

## Best Practices

### 1. Write Clear Descriptions

**Bad**:
```markdown
---
description: Helps with code
---
```

**Good**:
```markdown
---
description: Review code for security vulnerabilities and performance issues
---
```

### 2. Always Declare allowed-tools

**Bad**: Prompts for permission every time

**Good**:
```markdown
---
allowed-tools: [Bash(git:*), Read]
---
```

### 3. Use argument-hint

Helps users understand expected arguments:

```markdown
---
argument-hint: [source-branch] [target-branch]
---
```

### 4. Provide Context

Include relevant information for Claude:

```markdown
## Project Structure

!`tree -L 2 src/`

## Recent Changes

!`git log --oneline -5`

## Task

[Your command content]
```

### 5. Test with Various Inputs

Test your command with:
- No arguments: `/my-command`
- One argument: `/my-command arg1`
- Multiple arguments: `/my-command arg1 arg2 arg3`
- Special characters: `/my-command "arg with spaces"`

## Common Mistakes

### Mistake 1: Missing Descriptions

Commands without descriptions are hard to discover via `/help`.

**Solution**: Always add `description` in frontmatter.

### Mistake 2: Not Restricting Tools

Without `allowed-tools`, Claude will prompt for permission.

**Solution**: Explicitly list required tools.

### Mistake 3: Command Name Conflicts

Project commands override personal commands with same name.

**Solution**: Use subdirectories for namespacing.

### Mistake 4: Complex Multi-Step Workflows

Slash commands work best for simple, focused tasks.

**Solution**: For complex workflows, create a Skill instead.

### Mistake 5: Untested Arguments

`$ARGUMENTS` might be empty or contain unexpected values.

**Solution**: Test thoroughly and handle missing arguments gracefully.

## Slash Commands vs Skills

| Aspect | Slash Commands | Skills |
|--------|---|---|
| **Complexity** | Simple prompts | Complex workflows |
| **Files** | Single `.md` | Multiple files + scripts |
| **Discovery** | Manual (`/command`) | Automatic (context-based) |
| **Scope** | Project or personal | Project or personal |
| **Use case** | Frequently used prompts | Team workflows, expertise |

**Use slash commands for**:
- Quick templates
- Frequently-used instructions
- Simple git operations
- Reminders

**Use Skills for**:
- Multi-file capabilities
- Complex workflows
- Team standardization
- Organized reference material

## Quick Start

### Create a Simple Command

```bash
# Create command directory
mkdir -p .claude/commands

# Create command file
cat > .claude/commands/my-command.md << 'EOF'
---
description: My custom command
argument-hint: [input]
---

Process $ARGUMENTS according to project standards.
EOF

# Use it
/my-command test input
```

### Create a Git Commit Command

```bash
cat > .claude/commands/commit.md << 'EOF'
---
allowed-tools: [Bash(git add:*), Bash(git status:*), Bash(git commit:*)]
argument-hint: [message]
description: Create descriptive git commit
---

Current status: !`git status`

Create commit with message: $ARGUMENTS

Use conventional commits format.
EOF
```

### Create a Review Command

```bash
cat > .claude/commands/review.md << 'EOF'
---
allowed-tools: [Read, Grep]
argument-hint: [file-path]
description: Review file for issues
---

Review @$1 for:
- Code quality
- Security issues
- Performance problems
- Best practices

Provide detailed feedback.
EOF
```

## Debugging Commands

### Check Command Location

```bash
# List all commands
ls -R .claude/commands/
ls -R ~/.claude/commands/

# View command content
cat .claude/commands/my-command.md
```

### Test Arguments

```bash
# Add debug output in command
echo "Arguments: '$ARGUMENTS'" > /tmp/debug.log
echo "Arg1: '$1', Arg2: '$2'" >> /tmp/debug.log
```

### Verify Frontmatter

Ensure proper YAML syntax:
- Use spaces, not tabs
- Proper `---` delimiters
- Valid field names

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

## Examples from Practice

### Git Operations

```markdown
---
allowed-tools: [Bash(git:*)]
description: Create feature branch from main
argument-hint: [branch-name]
---

!`git checkout main`
!`git pull`
!`git checkout -b $ARGUMENTS`
```

### Documentation

```markdown
---
allowed-tools: [Read, Write]
description: Generate README for current directory
---

Analyze project structure: !`ls -la`

Create README.md with:
- Project description
- Installation steps
- Usage examples
- Contributing guidelines
```

### Testing

```markdown
---
allowed-tools: [Bash(pytest:*), Bash(npm:*)]
description: Run tests with coverage
---

Run tests: !`pytest --cov=src tests/`

Analyze coverage and suggest improvements.
```

## Command Organization

### By Category

```
.claude/commands/
├── git/
│   ├── commit.md
│   ├── branch.md
│   └── merge.md
├── code/
│   ├── review.md
│   ├── refactor.md
│   └── test.md
└── docs/
    ├── readme.md
    └── changelog.md
```

### By Tool

```
.claude/commands/
├── docker/
├── kubernetes/
├── terraform/
└── aws/
```

### By Workflow

```
.claude/commands/
├── setup/
├── develop/
├── test/
└── deploy/
```

## Additional Resources

- [Official Documentation](https://code.claude.com/docs/en/slash-commands.md)
- Skills: See [Claude Skills](../claude-skills/SKILL.md) for converting to Skills
