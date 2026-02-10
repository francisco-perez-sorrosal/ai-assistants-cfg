# Commands

Reusable slash commands for Claude Code. Each `.md` file becomes a `/command-name` invocable during interactive sessions.

## Available Commands

| Command | Description |
|---------|-------------|
| `/co` | Create a commit for staged (or all) changes |
| `/cop` | Create a commit and push to remote |
| `/create-worktree` | Create a new git worktree in `.trees/` |
| `/merge-worktree` | Merge a worktree branch back into current branch |
| `/create-simple-python-prj` | Create a basic Python project with pixi or uv |
| `/add-rules` | Copy rules into the current project for customization |
| `/manage-readme` | Create or refine README.md files |
| `/star-repo` | Star the ai-assistants-cfg repo on GitHub |

## How Commands Work

Commands are loaded automatically from `commands/` (plugin), `.claude/commands/` (project), or `~/.claude/commands/` (personal). Invoke with `/` prefix during interactive sessions.

For authoring guidance, see the [`command-crafting`](../skills/command-crafting/) skill.
