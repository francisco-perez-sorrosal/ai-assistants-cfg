# Workflow Patterns

Patterns for structuring multi-step skills that guide agents through complex operations. Reference material for the [Skill Creator](../SKILL.md) skill.

## Sequential Workflows

Use sequential workflows when the task has clear, ordered steps where each depends on the previous one. Provide an overview of the process early in SKILL.md so the agent understands the full picture before starting.

```markdown
## PDF Form Filling Process

Follow these steps in order:

1. **Analyze** the blank PDF form -- identify all fillable fields
2. **Map** source data to form fields -- create a field mapping
3. **Validate** the mapping -- run `scripts/validate_mapping.py`
4. **Fill** the form -- apply mapped values to fields
5. **Verify** the output -- confirm all fields populated correctly

After each step, check results before proceeding. If validation
fails, return to the mapping step and correct errors.
```

Include validation loops (run validator, fix errors, repeat) between steps where errors are likely. This dramatically improves output quality.

## Conditional Workflows

Use conditional workflows when the task has branching logic based on the current situation. Guide the agent through decision points with clear criteria.

```markdown
## Content Workflow

Determine the starting point:

**Creating new content?**
1. Gather requirements from the user
2. Create outline with target audience and scope
3. Draft content following the style guide
4. Run `scripts/check_style.py` on the draft

**Editing existing content?**
1. Read the current document and identify the change scope
2. Preserve voice and terminology already established
3. Make targeted edits -- avoid rewriting sections unnecessarily
4. Run `scripts/check_style.py` on changed sections only
```

Frame decision points as questions the agent can answer from context. Avoid deeply nested branches -- flatten with guard clauses or split into separate workflows when complexity grows.
