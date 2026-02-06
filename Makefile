SHELL := /bin/bash
CLAUDE := $(HOME)/.local/bin/claude

.PHONY: validate run install help

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

validate: ## Validate the plugin manifest
	$(CLAUDE) plugin validate .

run: validate ## Start Claude Code with the plugin (dev mode, no API key)
	unset ANTHROPIC_API_KEY && $(CLAUDE) --plugin-dir $(CURDIR)

install: ## Install Claude config + plugin via local marketplace
	./install.sh

status: ## Show what would be installed
	@echo "Plugin: i-am v$$(jq -r .version .claude-plugin/plugin.json)"
	@echo ""
	@echo "Skills:"
	@ls -1d skills/*/SKILL.md 2>/dev/null | sed 's|skills/\(.*\)/SKILL.md|  \1|'
	@echo ""
	@echo "Commands:"
	@ls -1 commands/*.md 2>/dev/null | sed 's|commands/\(.*\)\.md|  /\1|'
	@echo ""
	@echo "Agents:"
	@ls -1 agents/*.md 2>/dev/null | grep -v README.md | sed 's|agents/\(.*\)\.md|  \1|' || echo "  (none)"
