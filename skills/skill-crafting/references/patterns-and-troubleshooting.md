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
- Duplicating rule content in skills -- if a rule covers commit conventions, the skill should not repeat them. Claude loads both when relevant; duplication wastes tokens and creates sync divergence

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

### Plugin Reference File Permissions

**Symptom:** Claude prompts for permission every time it tries to read a satellite file from a plugin skill, or previously approved paths stop working after a plugin update.

**Cause:** `allowed-tools: [Read]` in frontmatter grants tool permission (Claude can use the Read tool) but not filesystem path permission. Plugin reference files live in `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/...` — a path outside the project directory. Claude treats reads to this path as requiring explicit approval. When the plugin updates, the version segment changes, invalidating all prior approvals.

**Fix:** Add a wildcard allowlist so Claude can read any file in the plugin cache without prompting:

```json
// settings.json or settings.local.json
{
  "permissions": {
    "additionalDirectories": ["~/.claude/plugins/**"]
  }
}
```

This grants read access to all installed plugin files. The wildcard covers version changes, so approvals survive plugin updates.

**Verification:** After adding the allowlist, activate a plugin skill and trigger a reference file read. Use `/context` to confirm the reference file was loaded without a permission prompt.
