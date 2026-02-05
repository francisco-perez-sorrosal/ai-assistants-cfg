# Slash Commands Skill

Skill for creating and managing slash commands — reusable, user-invoked prompts stored as Markdown files.

## What This Skill Does

When activated, this skill provides guidance for:

- **Creating commands** with proper frontmatter, arguments, and tool permissions
- **Choosing** between slash commands and skills for a given use case
- **Debugging** command behavior, argument substitution, and discovery issues
- **Organizing** commands with subdirectories and namespacing

## Activation

The skill activates automatically when Claude detects tasks related to:

- Creating custom slash commands
- Debugging command behavior or argument handling
- Converting prompts to reusable commands

You can also trigger it explicitly by asking about slash commands or referencing it by name.

## Skill Contents

| File | Purpose |
|------|---------|
| `SKILL.md` | Core reference: structure, frontmatter, arguments, features, best practices |
| `REFERENCE.md` | Extended examples: command patterns, real-world recipes, organization strategies |
| `README.md` | This file — overview and testing guide |

## Existing Commands in This Repository

Commands live in `.claude/commands/` and are available to any project that symlinks to this config (via `install.sh`).

| Command | Description |
|---------|-------------|
| `/co` | Create a commit for staged (or all) changes |
| `/cop` | Create a commit and push to remote |
| `/create_worktree` | Create a new git worktree in `.trees/` |
| `/merge_worktree` | Merge a worktree back from `.trees/` |
| `/create-simple-python-prj` | Create a basic Python project with pixi or uv |

## Testing

### In Claude Code (CLI)

**Test command creation guidance:**

```bash
# Start a Claude Code session
claude

# Ask to create a command — the skill should activate automatically
> I want to create a slash command for running my test suite

# Or reference it explicitly
> Using the slash-cmd skill, help me build a deploy command
```

**Test an existing command:**

```bash
# Invoke a command directly
/co fix typo in README

# Invoke with arguments
/create_worktree feature-auth
```

**Test command debugging:**

```bash
# Ask about argument issues
> My slash command isn't receiving arguments correctly, can you help?

# Ask about discovery
> Why doesn't my command show up in /help?
```

### Validation Checklist

After creating or modifying commands, verify:

- [ ] YAML frontmatter parses correctly (no tabs, proper `---` delimiters)
- [ ] `description` is specific and action-oriented
- [ ] `allowed-tools` is declared (avoids permission prompts)
- [ ] `argument-hint` matches expected usage
- [ ] Command activates when invoked with `/command-name`
- [ ] Arguments substitute correctly (`$ARGUMENTS`, `$1`, `$2`)
- [ ] Bash `!` commands and file `@` references resolve properly
