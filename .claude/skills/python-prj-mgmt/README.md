# Python Project Management Skill

Managing Python projects with modern package managers. Defaults to **pixi** unless uv is explicitly requested.

## When to Use

- Setting up a new Python project
- Managing dependencies (add, remove, update)
- Configuring environments and dependency groups
- Choosing between pixi and uv
- CI/CD integration for Python projects

## Activation

The skill activates automatically when the agent detects project management tasks: initializing projects, managing dependencies, configuring environments, or choosing package managers.

Trigger explicitly by mentioning "python project management," "pixi," or "uv."

## Skill Contents

| File | Purpose |
|------|---------|
| `SKILL.md` | Core reference: tool selection, project init, dependency management, CI/CD, pyproject.toml configs, best practices |
| `pixi.md` | Complete pixi reference: conda+PyPI ecosystem, environments, tasks, ML workflows, troubleshooting |
| `uv.md` | Complete uv reference: fast installs, Python version management, workspaces, build/publish |
| `README.md` | This file — overview and usage guide |

## Related Skills

- [Python Development](../python/SKILL.md) — type hints, testing, code quality, language patterns
