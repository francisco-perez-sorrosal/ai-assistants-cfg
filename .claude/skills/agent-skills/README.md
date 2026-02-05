# Agent Skills Skill

Meta-skill for creating and optimizing Agent Skills — the open format for extending AI agents with specialized knowledge and workflows.

## When to Use

- Creating a new skill from scratch
- Converting memory files or repeated prompts into reusable skills
- Debugging why a skill isn't activating or loading correctly
- Reviewing skill structure, naming, or description quality
- Understanding progressive disclosure, frontmatter fields, or the spec

For the official specification, see [agentskills.io](https://agentskills.io).

## Activation

The skill activates automatically when the agent detects tasks related to:

- Creating, authoring, or structuring skills
- Skill activation or discovery issues
- Questions about `SKILL.md` format, frontmatter, or best practices

Trigger explicitly by asking about "agent skills," "creating a skill," or referencing this skill by name.

## Skill Contents

| File | Purpose |
|------|---------|
| `SKILL.md` | Core reference: spec fields, naming, structure, progressive disclosure, content guidelines, development workflow, anti-patterns, checklist |
| `README.md` | This file — overview and usage guide |

## Quick Start

1. **Load the skill**: reference `agent-skills` when starting skill authoring work
2. **Create the directory**: `skill-name/SKILL.md` with required `name` and `description` frontmatter
3. **Write instructions**: concise body content — only what the agent doesn't already know
4. **Add supporting files** (optional): `scripts/`, `references/`, `assets/` as needed
5. **Test**: use the author-tester workflow (one instance writes, another tests on real tasks)
6. **Validate**: run through the deployment checklist in `SKILL.md`

## Testing

**Test skill creation guidance:**

```
# Ask about creating a skill — the skill should activate automatically
> I want to create a skill for reviewing pull requests

# Or reference it explicitly
> Using the agent-skills skill, help me structure a new data-analysis skill
```

**Test troubleshooting:**

```
> My custom skill isn't activating when I mention PDF processing
> What's wrong with this SKILL.md frontmatter?
```

**Validate a skill you've built:**

```bash
# Use the skills-ref CLI if available
skills-ref validate ./my-skill

# Or manually check against the checklist in SKILL.md
```
