SHELL := /bin/bash
CLAUDE := $(HOME)/.local/bin/claude

.PHONY: validate run install install-desktop install-cursor dry-run dry-run-cursor help

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

validate: ## Validate the plugin manifest
	$(CLAUDE) plugin validate .

run: validate ## Start Claude Code with the plugin (dev mode, no API key)
	unset ANTHROPIC_API_KEY && $(CLAUDE) --plugin-dir $(CURDIR)

install: ## Install Claude config + plugin via local marketplace (interactive)
	./install.sh

install-desktop: ## Install for Claude Desktop (MCP servers)
	./install.sh desktop

install-cursor: ## Install for Cursor (user profile; use ./install.sh cursor PATH for per-project)
	./install.sh cursor

dry-run: ## Dry-run: show what would be installed (Claude Code)
	./install.sh code --dry-run

dry-run-cursor: ## Dry-run: show what would be installed (Cursor)
	./install.sh cursor --dry-run
