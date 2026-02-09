#!/usr/bin/env bash

set -eo pipefail

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Usage ---

usage() {
    echo "Usage: $(basename "$0") [--claude] [--plugin] [--check] [--help]"
    echo ""
    echo "Install ai-assistants configuration for AI coding assistants."
    echo ""
    echo "Options:"
    echo "  --claude        Install Claude personal config (default when no flags given)"
    echo "  --plugin        Install/repair the i-am plugin only (skips config)"
    echo "  --check         Verify plugin health without modifying anything"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $(basename "$0")                # Install Claude config, prompt for plugin"
    echo "  $(basename "$0") --plugin       # Re-register marketplace and reinstall plugin"
    echo "  $(basename "$0") --check        # Verify plugin is healthy"
}

# --- Parse arguments ---

INSTALL_CLAUDE=false
INSTALL_PLUGIN=false
CHECK_ONLY=false
HAS_FLAGS=false

for arg in "$@"; do
    case "$arg" in
        --claude)      INSTALL_CLAUDE=true; HAS_FLAGS=true ;;
        --plugin)      INSTALL_PLUGIN=true; HAS_FLAGS=true ;;
        --check)       CHECK_ONLY=true; HAS_FLAGS=true ;;
        --help)        usage; exit 0 ;;
        *)
            echo "Unknown option: $arg"
            usage
            exit 1
            ;;
    esac
done

# Default: --claude when no flags given
if ! $HAS_FLAGS; then
    INSTALL_CLAUDE=true
fi

# --- Shared helpers ---

link_item() {
    local source="$1"
    local target="$2"
    local label="$3"

    echo "Linking ${label}"
    if [ -L "$target" ] && [ "$(readlink "$target")" = "$source" ]; then
        echo "  ✓ ${target} (already linked)"
        return 0
    fi

    if [ -e "$target" ]; then
        echo "  ! ${target} exists and would be overwritten"
        read -p "    Continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "    Skipped ${target}"
            return 0
        fi
    fi

    ln -sf "$source" "$target"
    echo "  - ${target} -> ${source}"
}

# --- Claude installation ---

install_claude() {
    local src_dir="${THIS_DIR}/.claude"
    local dest_dir="${HOME}/.claude"

    # Detect OS and set Claude Desktop config path
    local desktop_config_dir
    case "$(uname -s)" in
        Darwin) desktop_config_dir="${HOME}/Library/Application Support/Claude" ;;
        Linux)  desktop_config_dir="${HOME}/.config/Claude" ;;
        *)      echo "Unsupported OS: $(uname -s)"; exit 1 ;;
    esac

    mkdir -p "${dest_dir}"

    echo "Installing Claude personal config..."
    echo ""

    # Clean stale symlinks from previous installations (whole-directory and per-item)
    local stale_items=("skills" "commands" "agents" "commit-conventions.md" "rules/commit-conventions.md" "rules/git-commit-conventions.md" "rules/git-commit-rules.md" "rules/git-commit-message-format.md")
    for item in "${stale_items[@]}"; do
        local target="$dest_dir/$item"
        if [ -L "$target" ]; then
            echo "  Removing stale symlink: ${target}"
            rm "$target"
        fi
    done
    for subdir in skills commands; do
        local dest_subdir="$dest_dir/$subdir"
        if [ -d "$dest_subdir" ]; then
            for item in "$dest_subdir"/*; do
                if [ -L "$item" ]; then
                    echo "  Removing stale symlink: ${item}"
                    rm "$item"
                fi
            done
            rmdir "$dest_subdir" 2>/dev/null || true
        fi
    done

    # Symlink personal config files
    local config_items=("CLAUDE.md" "claude_desktop_config.json" "userPreferences.txt" "settings.local.json")
    for item in "${config_items[@]}"; do
        if [ -e "$src_dir/$item" ]; then
            link_item "$src_dir/$item" "$dest_dir/$item" "$item"
        else
            echo "  - ${item} not found, skipping"
        fi
    done

    # Link Claude Desktop config to official location
    local desktop_source="${dest_dir}/claude_desktop_config.json"
    local desktop_target="${desktop_config_dir}/claude_desktop_config.json"

    if [ -e "$desktop_source" ] || [ -L "$desktop_source" ]; then
        echo ""
        echo "Linking Claude Desktop config to official location..."
        if [ -L "$desktop_target" ] && [ "$(readlink "$desktop_target")" = "$desktop_source" ]; then
            echo "  ✓ ${desktop_target} (already linked)"
        elif [ -e "$desktop_target" ] || [ -L "$desktop_target" ]; then
            echo "  ! ${desktop_target} exists and would be replaced"
            read -p "    Remove existing and create symlink? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -f "$desktop_target"
                ln -s "$desktop_source" "$desktop_target"
                echo "  - ${desktop_target} -> ${desktop_source}"
            else
                echo "    Skipped ${desktop_target}"
            fi
        else
            ln -s "$desktop_source" "$desktop_target"
            echo "  - ${desktop_target} -> ${desktop_source}"
        fi
    fi

    # Install rules (link all .md files from source rules/ directory, recursively)
    local rules_src="${THIS_DIR}/rules"
    local rules_dir="${dest_dir}/rules"
    mkdir -p "${rules_dir}"
    echo ""
    echo "Installing rules..."
    while IFS= read -r rule; do
        local rel_path="${rule#"$rules_src"/}"
        local rel_dir="$(dirname "$rel_path")"
        [[ "$(basename "$rule")" == "README.md" ]] && continue
        [[ "$rel_path" == */references/* ]] && continue
        [ "$rel_dir" != "." ] && mkdir -p "${rules_dir}/${rel_dir}"
        link_item "$rule" "${rules_dir}/${rel_path}" "${rel_path} → rules/"
    done < <(find "$rules_src" -name '*.md' -type f | sort)

    echo ""
    echo "✓ Claude personal config installed"
}

# --- Plugin helpers ---

PLUGIN_NAME="i-am"
MARKETPLACE_NAME="bit-agora"
PLUGIN_CACHE_DIR="${HOME}/.claude/plugins/cache/${MARKETPLACE_NAME}/${PLUGIN_NAME}"

require_claude_cli() {
    if ! command -v claude &>/dev/null; then
        echo "  ! Claude Code CLI not found. Install it first, then re-run."
        return 1
    fi
}

plugin_is_orphaned() {
    local orphaned_marker
    orphaned_marker=$(find "$PLUGIN_CACHE_DIR" -name '.orphaned_at' 2>/dev/null | head -1)
    [ -n "$orphaned_marker" ]
}

plugin_is_installed() {
    local installed_file="${HOME}/.claude/plugins/installed_plugins.json"
    [ -f "$installed_file" ] && grep -q "${PLUGIN_NAME}@${MARKETPLACE_NAME}" "$installed_file"
}

marketplace_is_registered() {
    local known_file="${HOME}/.claude/plugins/known_marketplaces.json"
    [ -f "$known_file" ] && grep -q "${MARKETPLACE_NAME}" "$known_file"
}

# --- Plugin health check ---

check_plugin() {
    echo ""
    echo "Checking i-am plugin health..."

    require_claude_cli || return 1

    local healthy=true

    if marketplace_is_registered; then
        echo "  ✓ Marketplace '${MARKETPLACE_NAME}' is registered"
    else
        echo "  ✗ Marketplace '${MARKETPLACE_NAME}' is NOT registered"
        healthy=false
    fi

    if plugin_is_installed; then
        echo "  ✓ Plugin '${PLUGIN_NAME}@${MARKETPLACE_NAME}' is in installed_plugins.json"
    else
        echo "  ✗ Plugin '${PLUGIN_NAME}@${MARKETPLACE_NAME}' is NOT in installed_plugins.json"
        healthy=false
    fi

    if plugin_is_orphaned; then
        echo "  ✗ Plugin has an .orphaned_at marker (Claude Code won't load it)"
        healthy=false
    else
        echo "  ✓ No .orphaned_at marker"
    fi

    if [ -d "$PLUGIN_CACHE_DIR" ]; then
        echo "  ✓ Plugin cache directory exists"
    else
        echo "  ✗ Plugin cache directory missing"
        healthy=false
    fi

    echo ""
    if $healthy; then
        echo "✓ Plugin is healthy"
    else
        echo "✗ Plugin needs repair — run: ./install.sh --plugin"
    fi

    $healthy
}

# --- Hook installation ---

install_hooks() {
    local settings_file="${HOME}/.claude/settings.json"
    local hook_script="${THIS_DIR}/.claude-plugin/hooks/send_event.py"

    if [ ! -f "$hook_script" ]; then
        echo "  ! Hook script not found: ${hook_script}"
        return 1
    fi

    echo ""
    echo "Installing Task Chronograph hooks into ${settings_file}..."

    python3 - "$settings_file" "$hook_script" << 'PYEOF'
import json, sys

settings_path, hook_script = sys.argv[1], sys.argv[2]

try:
    with open(settings_path) as f:
        settings = json.load(f)
except FileNotFoundError:
    settings = {}

hook_entry = lambda matcher="": {
    "matcher": matcher,
    "hooks": [{
        "type": "command",
        "command": f"python3 {hook_script}",
        "timeout": 10,
        "async": True,
    }],
}

settings["hooks"] = {
    "SubagentStart": [hook_entry()],
    "SubagentStop": [hook_entry()],
    "PostToolUse": [hook_entry("Write|Edit")],
}

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")

PYEOF

    if [ $? -eq 0 ]; then
        echo "  ✓ Hooks installed (SubagentStart, SubagentStop, PostToolUse)"
    else
        echo "  ! Failed to install hooks"
        return 1
    fi
}

# --- Plugin installation via GitHub marketplace ---

install_plugin() {
    echo ""
    echo "Installing i-am plugin via GitHub marketplace..."

    require_claude_cli || return 1

    # Remove orphan marker if present (allows clean reinstall)
    if plugin_is_orphaned; then
        echo ""
        echo "Removing .orphaned_at marker from previous installation..."
        find "$PLUGIN_CACHE_DIR" -name '.orphaned_at' -delete 2>/dev/null
        echo "  ✓ Orphan marker removed"
    fi

    # Register marketplace (idempotent — re-register to ensure it's current)
    echo ""
    echo "Registering GitHub marketplace..."
    if claude plugin marketplace add francisco-perez-sorrosal/bit-agora 2>&1; then
        echo "  ✓ Marketplace registered"
    else
        echo "  ! Marketplace registration had warnings (may already exist)"
    fi

    # Install the plugin
    echo ""
    echo "Installing ${PLUGIN_NAME} from ${MARKETPLACE_NAME} marketplace..."
    if ! claude plugin install "${PLUGIN_NAME}@${MARKETPLACE_NAME}" --scope user 2>&1; then
        echo "  ! Plugin install command failed"
        return 1
    fi

    # Post-install verification
    echo ""
    echo "Verifying installation..."

    local ok=true

    if plugin_is_installed; then
        echo "  ✓ Plugin registered in installed_plugins.json"
    else
        echo "  ✗ Plugin NOT found in installed_plugins.json after install"
        ok=false
    fi

    if plugin_is_orphaned; then
        echo "  ✗ Plugin still has .orphaned_at marker after install"
        ok=false
    else
        echo "  ✓ No orphan marker"
    fi

    echo ""
    if $ok; then
        install_hooks
        echo ""
        echo "✓ i-am plugin installed and verified. Skills and commands available in all sessions."
    else
        echo "✗ Installation completed but verification found issues. Check output above."
        return 1
    fi
}

# --- Main ---

if $CHECK_ONLY; then
    check_plugin
    exit $?
fi

if $INSTALL_CLAUDE; then
    install_claude

    if ! $INSTALL_PLUGIN; then
        echo ""
        read -p "Also install the i-am claude plugin? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_plugin
        else
            echo ""
            echo "To install the plugin later, re-run: ./install.sh --plugin"
        fi
    fi
fi

if $INSTALL_PLUGIN; then
    install_plugin
fi
