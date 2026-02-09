# Common Patterns and Troubleshooting

Reference patterns for different skill types, anti-patterns to avoid, and troubleshooting common issues. Reference material for the [Agent Skills Development](../SKILL.md) skill.

## Common Patterns

### Read-Only Reference Skills

```yaml
allowed-tools: [Read, Grep, Glob]
```

For documentation and code analysis.

### Script-Based Skills

```yaml
allowed-tools: [Read, Bash, Write]
```

Reference scripts with forward slashes: `scripts/helper.py`

### Template-Based Skills

```yaml
allowed-tools: [Read, Write, Edit]
```

Store templates in `assets/` directory.

## Anti-Patterns

- Vague descriptions ("Helps with documents")
- Over-explaining what the agent already knows
- Windows-style paths -- use forward slashes everywhere
- Too many options -- provide one default with escape hatches
- Deeply nested references -- keep one level from `SKILL.md`
- Hard-referencing slash commands from skills -- commands are tool-specific and break portability. Describe the workflow outcome ("commit the changes") and let the agent's discovery mechanism find the right command. Cross-reference other skills instead; list commands in project-level files like `CLAUDE.md`
- Scripts that punt errors to the agent
- Time-based conditionals
- Voodoo constants without justification
- Assuming tools/packages are installed without listing them

## Troubleshooting

### Skill Not Activating

1. Verify description includes specific trigger terms
2. Check YAML syntax (spaces not tabs, proper `---` delimiters)
3. If `name` is present, confirm it matches directory name exactly
4. Test with explicit trigger phrases
5. Consult the specific agent's documentation for skill-loading behavior

### YAML Errors

- Use spaces, never tabs
- Quote strings with special characters
- `---` delimiters on their own lines

### Path Issues

- Use forward slashes everywhere
- Verify referenced paths exist
- Use `~` for home directory in personal skills
