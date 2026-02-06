# Skills

Reusable skill modules for Claude Code. Each skill is a self-contained directory with a `SKILL.md` that Claude loads automatically based on activation triggers.

## Available Skills

### Claude Code Authoring

| Skill | Description | When to Use |
|-------|-------------|-------------|
| **[agent-skills](agent-skills/)** | Creating and optimizing Agent Skills for Claude Code, Cursor, and other agents. Covers activation patterns, content structure, and progressive disclosure. | Creating new skills, updating/modernizing existing skills, debugging skill activation, understanding skill architecture. |
| **[agent-creator](agent-creator/)** | Building custom agents (subagents) with prompt writing, tool configuration, and lifecycle management. | Building custom agents, designing agent workflows, spawning subagents, delegating tasks to agents. |
| **[slash-cmd](slash-cmd/)** | Creating slash commands with proper syntax, arguments, frontmatter, and best practices. | Creating custom slash commands, debugging command behavior, converting prompts to reusable commands. |

### Software Development

| Skill | Description | When to Use |
|-------|-------------|-------------|
| **[python](python/)** | Modern Python development with type hints, testing patterns (pytest), and code quality tools (ruff, mypy). | Writing Python code, implementing tests, configuring tooling, discussing language features. |
| **[python-prj-mgmt](python-prj-mgmt/)** | Python project management with pixi and uv. Defaults to **pixi** unless uv is explicitly requested. | Setting up projects, managing dependencies, configuring environments, initializing new projects. |
| **[refactoring](refactoring/)** | Pragmatic refactoring emphasizing modularity, low coupling, high cohesion, and incremental improvement. | Restructuring code, improving design, reducing coupling, organizing codebases, eliminating code smells. |
| **[software-planning](software-planning/)** | Three-document planning model (PLAN.md, WIP.md, LEARNINGS.md) for tracking work in small, known-good increments. | Starting significant software work, breaking down complex tasks, multi-step development efforts. |

### Domain-Specific

| Skill | Description | When to Use |
|-------|-------------|-------------|
| **[ticker](ticker/)** | Look up stock ticker symbols from company names using Yahoo Finance. Caches results with 30-day TTL. | Researching stocks, needing ticker symbols, validating tickers, getting company details (sector, market cap). |
| **[stock-clusters](stock-clusters/)** | Analyze stocks by return and volatility using K-means clustering. Produces interactive HTML visualizations. | Exploring investment opportunities, identifying risk profiles, comparing market segments, analyzing portfolio positioning. |

## How Skills Work

Skills are loaded automatically when Claude detects a matching context based on each skill's `description` field in its frontmatter. You can also reference them explicitly (e.g., "load the `refactoring` skill").

### Activation

- **Automatic**: Claude matches your task context against skill `description` triggers
- **Explicit**: Reference a skill by name in conversation or from `CLAUDE.md`

### Structure

Each skill directory contains at minimum a `SKILL.md` with:
- **Frontmatter**: `name`, `description`, `allowed-tools`, and other metadata
- **Content**: Domain-specific guidance, patterns, and workflows

Larger skills use **progressive disclosure** with supporting files (`REFERENCE.md`, `EXAMPLES.md`, `BEST-PRACTICES.md`) loaded only when needed, keeping the context window efficient.

### Storage Locations

- **This repository**: `skills/` at the root (distributed as a plugin)
- **Consumer projects** (shared via git): `.claude/skills/`
- **Personal** (user-specific): `~/.claude/skills/`
