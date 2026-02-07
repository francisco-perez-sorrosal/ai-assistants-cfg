# Development Guidelines for Claude

## Core Philosophy

PRAGMATISM IS NON-NEGOTIABLE. Every single line of code must be written with a purpose. No exceptions. This is not a suggestion or a preference - it is the fundamental practice that enables all other principles in this document.

I follow an approach of high quality of design and coding, with a strong emphasis on behavior-driven development and object and functional programming principles when required. All work should be done in small, bold incremental changes that maintain a working state throughout development. Tests are required when the code is critical or when instructed.

## Response Style

- Prefer concise, direct responses. Add educational or clarifying sentences when the situation requires it due to complexity, obscurity, or user request.
- When developing, minimize unnecessary explanations unless requested by the user.
- If you need to explain code, do so in a separate message before editing.
- Wrap filenames and code identifiers with `backticks` in any markdown context.
- Prefer meaningful anchor text over raw URLs.
- Use bullet points for lists and checklists if user asks for tasks.

## Available Skills

Load skills when possible to adhere to the user's preferences and navigate their projects efficiently. Skills activate automatically based on context, but can also be loaded explicitly by name.

### AI Assistant Crafting

- `skill-crafting` — Creating, updating, or debugging skills and understanding skill architecture
- `agent-crafting` — Building custom agents (subagents), designing agent workflows, or delegating tasks
- `command-crafting` — Creating or debugging slash commands
- `mcp-crafting` — Building MCP servers in Python (tools, resources, prompts, transports, testing, deployment)
- `rule-crafting` — Creating, updating, or debugging rules and organizing rule files

### Software Development

- `python` — Writing Python code, tests, type hints, and configuring quality tools (ruff, mypy, pytest)
- `python-prj-mgmt` — Setting up Python projects and managing dependencies (defaults to **pixi**, uv on request)
- `refactoring` — Restructuring code, improving design, reducing coupling, eliminating code smells
- `software-planning` — Three-document planning model (PLAN.md, WIP.md, LEARNINGS.md) for significant work

### Domain-Specific

Additional skills may be available depending on the project. Discover them through skill activation triggers or by exploring the `skills/` directory.

## Available Agents

Agents are autonomous subprocesses delegated for complex tasks. Usage conventions (coordination, parallelism, boundaries) are in the `software-agents-usage` rule.

- `researcher` → `RESEARCH_FINDINGS.md`
- `systems-architect` → `SYSTEMS_PLAN.md`
- `implementation-planner` → `IMPLEMENTATION_PLAN.md`, `WIP.md`, `LEARNINGS.md`
- `context-engineer` → audit report + artifact changes

## Available Commands

Slash commands for common workflows:

- `/co` — Create a commit for staged (or all) changes
- `/cop` — Create a commit and push to remote
- `/create_worktree [branch]` — Create a new git worktree in `.trees/`
- `/merge_worktree [branch]` — Merge a worktree branch back into current branch
- `/create-simple-python-prj [name] [desc] [pkg-mgr] [dir]` — Scaffold a Python project

## Workflow

- For questions about Claude Code features or usage, use the Task tool with `subagent_type='claude-code-guide'` to consult official documentation.
- When executing build commands in any programming language, output to `/dev/null` to avoid creating binaries.
- Store temporary files in `tmp/` directory.
- Do not include claude authorship in the commit messages.
- When debugging and using print or log statements, prefix them with a comment marking them as being used for extra debug purposes; this way you can identify them later and remove them when they are not necessary.
- Use `pbcopy` and `pbpaste` for clipboard interaction.

## Working with Claude

- Update CLAUDE.md when introducing meaningful changes
- Ask "What do I wish I'd known at the start?" after significant changes
- Document gotchas, patterns, decisions, edge cases while context is fresh

## Personal Info

- Username: `@fperezsorrosal`. Refer to any actions performed by this user as "you."
- Email/github user: `fperezsorrosal@gmail.com`
- Github: `https://github.com/francisco-perez-sorrosal`

## Summary

The key is to write clean, testable, object-oriented/functional code that evolves the final system or systems through small, safe increments. Every change should be driven by a pursue of the desired behavior, and the implementation should be the simplest thing that makes the functionality to be achieved. Remember that simplicity doesn't mean sloppiness or naivete. When in doubt, favor simplicity and readability over cleverness.
