#!/usr/bin/env bash

set -eo pipefail

THIS_DIR="$(pwd)"
DEST_DIR="${HOME}/.claude"
SRC_DIR="${THIS_DIR}/.claude"

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

echo "✓ My Claude Stuff installed successfully"