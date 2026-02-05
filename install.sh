#!/usr/bin/env bash

set -eo pipefail

THIS_DIR="$(pwd)"
DEST_DIR="${HOME}/.claude"
SRC_DIR="${THIS_DIR}/.claude"

# Detect OS and set Claude Desktop config path
case "$(uname -s)" in
    Darwin)
        CLAUDE_DESKTOP_CONFIG_DIR="${HOME}/Library/Application Support/Claude"
        ;;
    Linux)
        CLAUDE_DESKTOP_CONFIG_DIR="${HOME}/.config/Claude"
        ;;
    *)
        echo "Unsupported OS: $(uname -s)"
        exit 1
        ;;
esac

mkdir -p "${DEST_DIR}"

# Function to create symlink with overwrite
link_item() {
    local item="$1"
    local source="$SRC_DIR/$item"
    local target="$DEST_DIR/$item"

    echo "Linking ${item} from ${source} to ${target}"
    # Check if target already exists and is the correct symlink
    if [ -L "$target" ] && [ "$(readlink "$target")" = "$source" ]; then
        echo "  ✓ ${target} (already linked)"
        return 0
    fi

    # Ask for confirmation if target exists
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
    echo "  - ${target} -> ${source} linked"
}

echo "Installing My Claude Stuff..."

# Process each item in .claude directory
for item in "$SRC_DIR"/*; do
    if [ -e "$item" ]; then
        basename_item="$(basename "$item")"
        link_item "$basename_item"
    fi
done

# Link Claude Desktop config file to official location
link_claude_desktop_config() {
    local source="${DEST_DIR}/claude_desktop_config.json"
    local target="${CLAUDE_DESKTOP_CONFIG_DIR}/claude_desktop_config.json"

    if [ ! -e "$source" ] && [ ! -L "$source" ]; then
        echo "  ! claude_desktop_config.json not found in ${DEST_DIR}, skipping"
        return 0
    fi

    echo "Linking Claude Desktop config to official location..."
    if [ -L "$target" ] && [ "$(readlink "$target")" = "$source" ]; then
        echo "  ✓ ${target} (already linked)"
        return 0
    fi

    if [ -e "$target" ] || [ -L "$target" ]; then
        echo "  ! ${target} exists and would be replaced"
        read -p "    Remove existing file and create symlink? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "    Skipped ${target}"
            return 0
        fi
        rm -f "$target"
    fi

    ln -s "$source" "$target"
    echo "  - ${target} -> ${source} linked"
}

link_claude_desktop_config

echo "✓ My Claude Stuff installed successfully"