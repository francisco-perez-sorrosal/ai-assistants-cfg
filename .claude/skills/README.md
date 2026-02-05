# Skills

Reusable skill modules for Claude Code. Each skill is a self-contained directory with a `SKILL.md` that Claude loads automatically based on activation triggers.

## Available Skills

### Claude Code Authoring

| Skill | When to Use |
|-------|-------------|
| **[agent-skills](agent-skills/)** | Creating new skills, converting memory files to skills, debugging skill activation, or understanding skill architecture. |
| **[agent-creator](agent-creator/)** | Building custom agents (subagents), designing agent workflows, spawning subagents, or delegating tasks to agents. |
| **[slash-cmd](slash-cmd/)** | Creating custom slash commands, debugging command behavior, or converting prompts to reusable commands. |

### Software Development

| Skill | When to Use |
|-------|-------------|
| **[python](python/)** | Writing Python code, implementing tests, or needing guidance on type hints, testing frameworks, and code quality tools. |
| **[python-prj-mgmt](python-prj-mgmt/)** | Setting up Python projects, managing dependencies, or configuring environments. Defaults to pixi unless uv is requested. |
| **[refactoring](refactoring/)** | Restructuring code, improving design, reducing coupling, or organizing codebases for better maintainability. |
| **[software-planning](software-planning/)** | Starting significant software work that needs a three-document model (PLAN.md, WIP.md, LEARNINGS.md) for tracking progress. |

## How Skills Work

Skills are loaded automatically when Claude detects a matching context based on each skill's `activation` field in its frontmatter. You can also reference them explicitly from `CLAUDE.md` (e.g., "load the `refactoring` skill").

Each skill directory contains at minimum a `SKILL.md` with frontmatter (`description`, `activation`) and content that Claude uses as domain-specific guidance. Larger skills use progressive disclosure with supporting files (e.g., `REFERENCE.md`, `EXAMPLES.md`) loaded on demand.
