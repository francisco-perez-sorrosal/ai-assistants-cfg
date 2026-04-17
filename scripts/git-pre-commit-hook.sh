#!/usr/bin/env bash
# Git pre-commit hook: shipped-artifact isolation check.
#
# Blocks the commit if any staged Markdown file under a shipped surface
# (rules/, skills/, agents/, commands/, claude/config/) references a
# specific .ai-state/ or .ai-work/ entry. Test fixtures under
# **/tests/fixtures/** are excluded. Intentional exceptions: add
#   <!-- shipped-artifact-isolation:ignore -->
# on the same line.
#
# See rules/swe/shipped-artifact-isolation.md for the full rule.
#
# Installed by install_claude.sh into .git/hooks/pre-commit.

set -eo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$REPO_ROOT" ]; then
    exit 0
fi

CHECK_SCRIPT="$REPO_ROOT/scripts/check_shipped_artifact_isolation.py"
if [ ! -f "$CHECK_SCRIPT" ]; then
    exit 0
fi

# Collect staged .md files under shipped surfaces (Added, Copied, Modified,
# Renamed; ignores deletions).
STAGED="$(git diff --cached --name-only --diff-filter=ACMR \
    | grep -E '^(rules|skills|agents|commands|claude/config)/.*\.md$' \
    || true)"

if [ -z "$STAGED" ]; then
    exit 0
fi

# Split into argv (one path per arg; handles paths without spaces, which is
# the Praxion convention).
# shellcheck disable=SC2086
if ! python3 "$CHECK_SCRIPT" --repo-root "$REPO_ROOT" --files $STAGED; then
    cat >&2 <<'EOF'

error: shipped-artifact isolation violation(s) detected in staged files.

  Shipped surfaces (rules/, skills/, agents/, commands/, claude/config/) must
  not reference specific .ai-state/ or .ai-work/ entries -- those are
  per-project meta-state and would dangle when the plugin installs elsewhere.

  Fix the flagged lines, or -- if the reference is genuinely intentional --
  append this marker to the same line:

      <!-- shipped-artifact-isolation:ignore -->

  Rule:           rules/swe/shipped-artifact-isolation.md
  Bypass (risky): git commit --no-verify
EOF
    exit 1
fi

exit 0
