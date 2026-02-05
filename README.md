# Assistant Config

TODO: Integrate in my .i-am project after polishing it enough.

## Installation

Run `./install.sh` to symlink the `.claude` directory contents to `~/.claude`.

### Claude Desktop Config

The installer also links `claude_desktop_config.json` to the official Claude Desktop location:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

This creates a symlink chain: `<official location>` → `~/.claude/claude_desktop_config.json` → `<project>/.claude/claude_desktop_config.json`, allowing you to version control your Claude Desktop preferences.

## References

https://code.claude.com/docs/en/sub-agents
https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices.md
https://github.com/bendrucker/claude/blob/main/.claude/
https://github.com/citypaul/.dotfiles/blob/main/claude