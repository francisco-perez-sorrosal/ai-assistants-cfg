# Claude installer config

Resources used by `install_claude.sh` (and the main installer when targeting Claude Code or Claude Desktop).

- **config_items.txt** — One filename per line. Files in this directory that are listed here are symlinked into `~/.claude/` during install. Only existing files are linked (e.g. `settings.local.json` is optional).

- **stale_symlinks.txt** — One path per line (relative to `~/.claude/`). During install, these are removed if they are symlinks (legacy cleanup).

- **CLAUDE.md**, **userPreferences.txt**, **claude_desktop_config.json** — Personal config files linked to `~/.claude/`. Add **settings.local.json** here if you want it installed by default.
