SHELL := /bin/bash
CLAUDE := $(HOME)/.local/bin/claude

.PHONY: validate run install install-claude install-claude-code install-cursor dry-run dry-run-claude dry-run-cursor help

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

validate: ## Validate the plugin manifest
	$(CLAUDE) plugin validate .

run: validate ## Start Claude Code with the plugin (dev mode, no API key)
	unset ANTHROPIC_API_KEY && $(CLAUDE) --plugin-dir $(CURDIR)

install: ## Default: Claude config + plugin via local marketplace (interactive)
	./install.sh

install-claude: ## Install Claude config + plugin via local marketplace
	./install.sh

install-claude-code: ## Install for Claude Code (./install.sh code)
	./install.sh code

install-cursor: ## Install for Cursor (user profile ~/.cursor/ or pass path)
	./install.sh cursor

dry-run: ## Dry-run for default target (Claude Code): show what would be installed
	./install.sh code --dry-run

dry-run-claude: ## Dry-run: show what would be installed for Claude (code)
	./install.sh code --dry-run

dry-run-cursor: ## Dry-run: show what would be installed for Cursor
	./install.sh cursor --dry-run
