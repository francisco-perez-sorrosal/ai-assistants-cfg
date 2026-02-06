#!/usr/bin/env bash

set -eo pipefail

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Usage ---

usage() {
    echo "Usage: $(basename "$0") [--claude] [--help]"
    echo ""
    echo "Install ai-assistants configuration for AI coding assistants."
    echo ""
    echo "Options:"
    echo "  --claude        Install Claude personal config (default)"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $(basename "$0")                # Install Claude config"
}

# --- Parse arguments ---

INSTALL_CLAUDE=true

for arg in "$@"; do
    case "$arg" in
        --claude)      INSTALL_CLAUDE=true ;;
        --help)        usage; exit 0 ;;
        *)
            echo "Unknown option: $arg"
            usage
            exit 1
            ;;
    esac
done

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
        [ "$rel_dir" != "." ] && mkdir -p "${rules_dir}/${rel_dir}"
        link_item "$rule" "${rules_dir}/${rel_path}" "${rel_path} → rules/"
    done < <(find "$rules_src" -name '*.md' -type f | sort)

    echo ""
    echo "✓ Claude personal config installed"
}

# --- Plugin installation via local marketplace ---

install_plugin() {
    echo ""
    echo "Installing i-am plugin via local marketplace..."

    if ! command -v claude &>/dev/null; then
        echo "  ! Claude Code CLI not found. Install it first, then re-run."
        return 1
    fi

    # Validate the plugin manifest
    claude plugin validate "${THIS_DIR}" 2>&1

    # Register this repo as a local marketplace
    echo ""
    echo "Registering local marketplace..."
    claude plugin marketplace add "${THIS_DIR}" 2>&1 \
        || echo "  (marketplace may already be registered)"

    # Install the plugin from the marketplace
    echo ""
    echo "Installing i-am from bit-agora marketplace..."
    claude plugin install i-am@bit-agora --scope user 2>&1

    echo ""
    echo "✓ i-am plugin installed. Skills and commands available in all sessions."
}

# --- Main ---

if $INSTALL_CLAUDE; then
    install_claude

    echo ""
    read -p "Also install the i-am claude plugin? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_plugin
    else
        echo ""
        echo "To install the plugin later, re-run: ./install.sh"
    fi
fi
