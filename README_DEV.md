# Developer Guide

Contributor and developer documentation for ai-assistants. For installation and usage, see [`README.md`](README.md).

## Project Structure

```
skills/                              # Shared skill modules (assistant-agnostic)
├── skill-crafting/
├── agent-crafting/
├── command-crafting/
├── mcp-crafting/
├── rule-crafting/
├── python-development/
├── python-prj-mgmt/
├── refactoring/
├── code-review/
├── software-planning/
└── doc-management/
commands/                            # Shared slash commands
├── add-rules.md
├── co.md
├── cop.md
├── create-simple-python-prj.md
├── create-worktree.md
├── manage-readme.md
└── merge-worktree.md
agents/                              # Shared agent definitions
├── promethean.md
├── researcher.md
├── systems-architect.md
├── implementation-planner.md
├── context-engineer.md
├── implementer.md
├── verifier.md
├── doc-engineer.md
└── sentinel.md
rules/                               # Rules (installed to ~/.claude/rules/)
├── swe/
│   ├── agent-intermediate-documents.md
│   ├── coding-style.md
│   ├── software-agents-usage.md
│   └── vcs/
│       ├── git-commit-message-format.md
│       └── git-commit-hygiene.md
└── writing/
    └── readme-style.md
.claude-plugin/                      # Claude Code plugin manifest
├── plugin.json
└── PLUGIN_SCHEMA_NOTES.md
.claude/                             # Claude personal config (symlinked to ~/.claude/)
├── CLAUDE.md
├── claude_desktop_config.json
├── userPreferences.txt
└── settings.local.json              # gitignored
task-chronograph-mcp/                # Pipeline observability MCP server
install.sh                           # Multi-assistant installer
```

## Working on this Repo

- When adding or modifying skills, load the `skill-crafting` skill for spec compliance
- When adding or modifying commands, load the `command-crafting` skill
- When adding or modifying agents, load the `agent-crafting` skill
- When adding or modifying rules, load the `rule-crafting` skill
- Follow commit conventions in `rules/` (auto-loaded by Claude when relevant)
- **Never modify `~/.claude/plugins/cache/`** -- it contains installed copies that get overwritten on reinstall; always edit source files in this repo
- **Token budget**: Always-loaded content (CLAUDE.md files + rules) must stay under 8,500 tokens (~29,750 chars). Before adding a new rule, verify the budget. Prefer skills with reference files for procedural content; reserve rules for declarative domain knowledge

## Design Intent

- **Assistant-agnostic shared assets**: `skills/`, `commands/`, `agents/` live at the repo root, reusable across any AI assistant
- **Assistant-specific config**: Personal settings live in assistant directories (`.claude/` for Claude, future `.chatgpt/` etc.)
- **Plugin distribution**: Skills, commands, and agents are installed via Claude Code's plugin system (`.claude-plugin/plugin.json`)
- **Symlink for personal config**: `install.sh` symlinks assistant-specific config to the expected locations
- **Progressive disclosure**: Skills load metadata at startup, full content on activation, reference files on demand
- **CLAUDE.md stays lean**: Skills, commands, agents, and rules are auto-discovered by Claude via filesystem scanning -- listing them in `CLAUDE.md` wastes always-loaded tokens and creates a sync burden. `README.md` and per-directory READMEs serve as the human-facing catalogs

## How Rules Interact with Commands

Rules do **not** need to be referenced from slash commands. When `/co` triggers a commit workflow, Claude automatically loads relevant rules from `~/.claude/rules/` based on the task context -- no explicit binding required.

Commands can use **semantic hints** to help Claude disambiguate when multiple overlapping rules exist:

```
"Commit following our conventional commits standard."
```

Never reference rule filenames directly in commands -- filenames have no special meaning to the command system.

See [`rules/README.md`](rules/README.md) for the full rule specification, writing guidelines, and the rules-vs-skills-vs-CLAUDE.md decision model.

## install.sh

The installer handles two concerns: personal config and plugin installation.

```bash
./install.sh              # Install Claude config, prompt for plugin
./install.sh --plugin     # Re-register marketplace and reinstall plugin
./install.sh --check      # Verify plugin health without modifying anything
./install.sh --help       # Show all options
```

**What gets installed:**

| Source (`.claude/`) | Target (`~/.claude/`) | Purpose |
|---------------------|----------------------|---------|
| `CLAUDE.md` | `~/.claude/CLAUDE.md` | Global development guidelines, code style, available skills and commands |
| `claude_desktop_config.json` | `~/.claude/claude_desktop_config.json` | Claude Desktop settings (MCP servers) |
| `userPreferences.txt` | `~/.claude/userPreferences.txt` | Adaptive precision mode -- controls response style and verbosity |
| `settings.local.json` | `~/.claude/settings.local.json` | Local permission settings (gitignored) |
| `rules/*.md` | `~/.claude/rules/*.md` | Rules (auto-linked, auto-loaded by Claude when relevant) |

The installer also links `claude_desktop_config.json` to the official Claude Desktop location:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

## Plugin Development

The plugin manifest lives in `.claude-plugin/plugin.json`. Key constraints:

- See `.claude-plugin/PLUGIN_SCHEMA_NOTES.md` for validator constraints
- The plugin is distributed via the [`bit-agora`](https://github.com/francisco-perez-sorrosal/bit-agora) GitHub marketplace
- When installed, commands are namespaced as `/i-am:<name>`

To test locally without installing:

```bash
claude --plugin-dir /path/to/ai-assistants
```

## References

- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
- [Claude Code Sub-agents](https://code.claude.com/docs/en/sub-agents)
- [Agent Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices.md)
- [bendrucker/claude config](https://github.com/bendrucker/claude/blob/main/.claude/)
- [citypaul/.dotfiles claude config](https://github.com/citypaul/.dotfiles/blob/main/claude)
