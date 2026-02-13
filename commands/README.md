# Commands

Reusable slash commands for Claude Code. Each `.md` file becomes a `/command-name` invocable during interactive sessions.

## Available Commands

| Command | Description |
|---------|-------------|
| `/add-rules` | Copy rules into the current project for customization |
| `/clean-work` | Clean the `.ai-work/` directory after pipeline completion |
| `/co` | Create a commit for staged (or all) changes |
| `/cop` | Create a commit and push to remote |
| `/create-simple-python-prj` | Create a basic Python project with pixi or uv |
| `/create-worktree` | Create a new git worktree in `.trees/` |
| `/manage-readme` | Create or refine README.md files |
| `/memory` | Manage persistent memory (user prefs, assistant learnings, project conventions) |
| `/merge-worktree` | Merge a worktree branch back into current branch |
| `/onboard-project` | Onboard the current project for the ai-assistants plugin ecosystem |
| `/star-repo` | Star the ai-assistants-cfg repo on GitHub |

## How Commands Work

Commands are loaded automatically from `commands/` (plugin), `.claude/commands/` (project), or `~/.claude/commands/` (personal). Invoke with `/` prefix during interactive sessions.

For authoring guidance, see the [`command-crafting`](../skills/command-crafting/) skill.
