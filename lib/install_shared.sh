#!/usr/bin/env bash
# Shared helper functions for Praxion installers.
#
# Sourced by install_claude.sh and install_cursor.sh. Must not be executed directly.
# Contains linking logic shared across assistant-specific installers (Claude Code,
# Cursor, etc.) to avoid duplication.
#
# Each function takes explicit parameters — no reliance on caller's variables.

# Guard against direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: this script must be sourced, not executed directly." >&2
    exit 1
fi

# =============================================================================
# Rules linking
# =============================================================================

# Symlink rule files from the repo's rules/ directory into a target rules directory.
#
# Both Claude Code and Cursor use the same rules source with the same filtering
# (skip README.md, skip references/), but link into different destinations:
#   - Claude Code: ~/.claude/rules/
#   - Cursor:      ~/.cursor/rules/ or <project>/.cursor/rules/
#
# This function is the single source of truth for which rule files get linked
# and how the directory structure is preserved.
#
# Arguments:
#   $1 — rules_source_dir: absolute path to the repo's rules/ directory
#   $2 — rules_target_dir: absolute path to the destination rules directory
#
# Output:
#   Prints nothing on success. Returns the count via the LINK_RULES_COUNT variable.
#   Creates target subdirectories as needed.
link_rules() {
    local rules_source_dir="$1"
    local rules_target_dir="$2"

    if [ ! -d "$rules_source_dir" ]; then
        echo "Error: rules source directory not found: $rules_source_dir" >&2
        return 1
    fi

    mkdir -p "$rules_target_dir"

    # Build the set of rule paths to skip during symlinking.
    # Rules with install: hook-deliver are NOT symlinked — they are injected
    # at session start by hooks/inject_rules.py, which reads the same manifest
    # and emits them as additionalContext. Symlinking them in addition would
    # load them unconditionally and defeat the per-project blacklist mechanism.
    local hook_deliver_paths=""
    local manifest_file="${rules_source_dir}/_manifest.yaml"
    if [ -f "$manifest_file" ]; then
        hook_deliver_paths=$(python3 - "$manifest_file" <<'PYEOF' 2>/dev/null
import yaml, sys
try:
    with open(sys.argv[1]) as f:
        m = yaml.safe_load(f)
    for r in m.get("rules", []):
        if r.get("install") == "hook-deliver":
            print(r["path"])
except Exception as e:
    sys.stderr.write(f"[link_rules] manifest parse failed: {e}; linking all rules\n")
PYEOF
        )
    fi

    LINK_RULES_COUNT=0
    while IFS= read -r rule_file; do
        local rel_path="${rule_file#"$rules_source_dir"/}"
        local rel_dir
        rel_dir="$(dirname "$rel_path")"

        # Skip non-rule files that live alongside rules
        [[ "$(basename "$rule_file")" == "README.md" ]] && continue
        # Reference files are skill/rule support material, not rules themselves
        [[ "$rel_path" == */references/* ]] && continue
        # Skip hook-deliver rules — delivered by inject_rules.py at session start
        if [ -n "$hook_deliver_paths" ]; then
            local rule_repo_path="rules/${rel_path}"
            if echo "$hook_deliver_paths" | grep -qxF "$rule_repo_path"; then
                continue
            fi
        fi

        [ "$rel_dir" != "." ] && mkdir -p "${rules_target_dir}/${rel_dir}"
        ln -sf "$rule_file" "${rules_target_dir}/${rel_path}"
        LINK_RULES_COUNT=$((LINK_RULES_COUNT + 1))
    done < <(find "$rules_source_dir" -name '*.md' -type f | sort)
}
