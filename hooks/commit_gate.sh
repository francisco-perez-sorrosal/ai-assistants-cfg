#!/bin/sh
# Fast-path gate for PreToolUse hooks that only apply to git commit commands.
# Reads stdin, checks for "git commit" with grep (< 1ms), and only invokes
# the Python hook if the payload looks like a commit. Avoids ~200-500ms of
# Python startup overhead on every non-commit Bash call.
#
# Usage: commit_gate.sh <python-hook-script>

set -e

# Honor the project-level memory opt-out. When PRAXION_DISABLE_MEMORY_MCP=1,
# the memory-protocol rule forbids agents from calling remember(); blocking
# their commits for not calling it would leave them with no legal path forward.
if [ "${PRAXION_DISABLE_MEMORY_MCP:-}" = "1" ]; then
    exit 0
fi

input=$(cat)

# Quick text check — the JSON payload contains "git commit" in the command field.
# False positives (rare) just run the Python hook unnecessarily — same as before.
if echo "$input" | grep -q 'git.*commit'; then
    echo "$input" | python3 "$1"
else
    exit 0
fi
