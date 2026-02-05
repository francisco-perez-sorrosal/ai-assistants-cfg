# Development Guidelines for Claude

## Core Philosophy

PRAGMATISM IS NON-NEGOTIABLE. Every single line of code must be written with a purpose. No exceptions. This is not a suggestion or a preference - it is the fundamental practice that enables all other principles in this document.

I follow an approach of high quality of desing and coding, with a strong emphasis on behavior-driven development and object and functional programming principles when required. All work should be done in small, bold incremental changes that maintain a working state throughout development. Tests are required when the code is critical or when instructed.

## Code Style

**Core principle**: Object and functional programming with immutable data when possible. Self-documenting code.

- Prefer concise, and direct responses. Add educational, clarifying sentences when situation requires due to complexity, obscure, or requested by the user.
- When developing, minimize unnecessary explanations unless requested by the user.
- Use natural line breaks unless the surrounding code is wrapped at a specific column.
- Wrap filenames and code identifiers with `backticks` in any markdown context.
- Include a trailing newline in all new files.
- Prefer meaningful anchor text over raw URLs.
- Use bullet points for lists and checklists if user asks for tasks.
- Write always readable code so it is as self-explanatory as possible.
- Use code comments ONLY to clarify complex or non-trivial algorithms or obscure language idioms to OTHER readers. If you need to explain the code, do so in a separate message before editing.

For refactoring tasks, load the `refactoring` skill.
For substantial work that requires extensive thought, load the `software-planning` skill for three-document model (PLAN.md, WIP.md, LEARNINGS.md).

## Code Organization

- Always modularize and structure the codebase. Provide meaningful names for packages and keep them well-scoped, but not overly small.
- Avoid creating or adding to catch-all packages/modules like `utils` or similar. Only when a particular module is getting too big, separate the utilities for that module in a `<module_name>_utils` file. Only use `utils` when a utility function is so generic that doesn't make any sense to place it anywhere else.
- Break code into multiple files where appropriate first before splitting across directories.

## Workflow

- The user has curated skills for his common workflows. Load skills when possible to adhere to the user's preferences and navigate their projects efficiently.
- For questions about Claude Code features or usage, use the Task tool with `subagent_type='claude-code-guide'` to consult official documentation.
- When executing build commands in any programming language, output to `/dev/null` to avoid creating binaries.
- Store temporary files in `tmp/` directory.
- Do not include claude authorship in the commit messages.
- When debuging and using print or log statements, prefix them with a comment marking them as being used for extra debug purposes; this way you can identify them later and remove them when they are not necessary.
- Use `pbcopy` and `pbpaste` for clipboard interaction.

## Working with Claude

- Update CLAUDE.md when introducing meaningful changes
- Ask "What do I wish I'd known at the start?" after significant changes
- Document gotchas, patterns, decisions, edge cases while context is fresh

For refactoring tasks, load the `refactoring` skill.
For substantial work that requires extensive thought, load the `software-planning` skill for three-document model (PLAN.md, WIP.md, LEARNINGS.md).

## Personal Info

- Username: `@fperezsorrosal`. Refer to any actions performed by this user as "you."
- Email/github user: `fperezsorrosal@gmail.com`
- Github: `https://github.com/francisco-perez-sorrosal`

## Summary

The key is to write clean, testable, object-oriented/functional code that evolves the final system or systems through small, safe increments. Every change should be driven by a pursue of the desired behavior, and the implementation should be the simplest thing that makes the functionality to be achieved. Remember that simplicity doesn't mean slopyness or naivete. When in doubt, favor simplicity and readability over cleverness.
