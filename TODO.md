# TODO

## Watch

### Local plugin persistence may break after CLI updates

**Issue**: [anthropics/claude-code#17089](https://github.com/anthropics/claude-code/issues/17089)

Locally installed plugins (via marketplace) sometimes stop loading after Claude Code CLI updates. If skills/commands disappear after an update, re-run `./install.sh` and choose to install the plugin again.

## Resolved Workarounds

### ~~Plugin skills not visible as slash commands~~

**Issue**: [anthropics/claude-code#17271](https://github.com/anthropics/claude-code/issues/17271)
**Related**: [anthropics/claude-code#16575](https://github.com/anthropics/claude-code/issues/16575)

**Status**: Fixed in Claude Code v2.1.29+. Workaround fully reverted.

The only permanent change kept from the investigation: `name` field removed from skill frontmatters (not needed — Claude Code uses the filename for command naming).
