# Python Skill

Conventions and preferences for modern Python development — type hints, testing, code quality tools, and project structure.

## When to Use

- Writing Python code in any project
- Setting up testing with pytest
- Configuring code quality tools (ruff, mypy)
- Choosing between dataclasses and Pydantic
- Structuring a Python package with `src` layout

## Activation

The skill activates automatically when the agent detects Python development tasks: writing code, implementing tests, discussing language features, or configuring tooling.

Trigger explicitly by mentioning "python skill" or referencing it by name.

## Skill Contents

| File | Purpose |
|------|---------|
| `SKILL.md` | Core reference: project structure, type hints, code style, data modeling, testing, tool configs, development workflow |
| `README.md` | This file — overview and usage guide |

## Related Skills

- [`python-prj-mgmt`](../python-prj-mgmt/SKILL.md) -- pixi/uv setup, dependency management, environment configuration
- [`refactoring`](../refactoring/SKILL.md) -- restructuring code, improving design, reducing coupling
