# Documentation Skill

Writing and maintaining project documentation with cross-reference validation, catalog maintenance, and freshness detection.

## When to Use

- Creating or refining README.md files
- Maintaining catalog READMEs (listing skills, agents, commands, rules)
- Validating cross-references in documentation (paths, links, counts, names)
- Detecting stale documentation after codebase changes
- Ensuring documentation matches the current filesystem state
- Auditing documentation quality across a project

## Activation

The skill activates automatically when the agent detects documentation tasks: README writing, documentation review, catalog maintenance, cross-reference validation, or documentation freshness assessment.

Trigger explicitly by mentioning "documentation skill" or referencing it by name.

## Skill Contents

| File | Purpose |
|------|---------|
| `SKILL.md` | Core reference: principles, README authoring workflow, cross-reference validation, catalog maintenance, freshness indicators, checklist |
| `references/cross-reference-patterns.md` | Detailed cross-reference validation procedures, catalog sync patterns, common drift scenarios, automated checking approaches |
| `references/documentation-types.md` | Per-type guidelines for README, architecture, changelog, contributing, and API documentation |
| `README.md` | This file -- overview and usage guide |

## Related Artifacts

- [`readme-style` rule](../../rules/writing/readme-style.md) -- Documentation conventions (WHAT to check: writing style, structural integrity, naming consistency)
- [`manage-readme` command](../../commands/manage-readme.md) -- Quick README creation and refinement (user-invoked action)
- [`doc-engineer` agent](../../agents/doc-engineer.md) -- Autonomous documentation quality management (loads this skill)
- [`sentinel` agent](../../agents/sentinel.md) -- Ecosystem-wide auditing that detects documentation drift
