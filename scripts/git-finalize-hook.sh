#!/usr/bin/env bash
# scripts/git-finalize-hook.sh — multiplexed git hook entry point.
#
# A single script handles three triggers: post-merge, post-commit, post-checkout.
# Each `.git/hooks/<name>` is a symlink to this file; dispatch is by the
# basename of the invocation path ($0). This collapses what would otherwise be
# three near-identical hook scripts into one.
#
# Trigger coverage (state-driven, not event-driven):
#
#   post-merge     — every git merge (ff and non-ff, pull, squash). Runs the
#                    full chain: reconcile + finalize-on-main + squash-safety.
#   post-commit    — every commit object created on the current branch. Runs
#                    finalize when on main with drafts present. Catches direct
#                    commits, non-ff merges (merge commit), rebases, cherry-picks.
#   post-checkout  — every branch switch (or fresh clone). Runs finalize when
#                    arriving on main with drafts present. Catches the case
#                    where drafts arrive without a local commit.
#
# Together the three cover every path that lands drafts on main, regardless
# of the git operation that put them there. All logic lives in finalize_chain.sh.
#
# Installed by install_claude.sh (Praxion self-install) and /onboard-project
# Phase 4 (user projects). Three symlinks point here.

set -eo pipefail

# Resolve the directory containing this script, following any symlinks.
# When invoked via .git/hooks/<name> -> scripts/git-finalize-hook.sh, the
# resolution finds the plugin's scripts/ directory where finalize_chain.sh
# and the python scripts live as siblings.
_resolve_script_dir() {
    local source="$1"
    while [ -L "$source" ]; do
        local target
        target="$(readlink "$source")"
        case "$target" in
            /*) source="$target" ;;
            *) source="$(cd -P "$(dirname "$source")" >/dev/null 2>&1 && pwd)/$target" ;;
        esac
    done
    (cd -P "$(dirname "$source")" >/dev/null 2>&1 && pwd)
}

# shellcheck source=./finalize_chain.sh
. "$(_resolve_script_dir "${BASH_SOURCE[0]}")/finalize_chain.sh"

# Dispatch by basename of $0. When git invokes .git/hooks/post-merge (a
# symlink to this script), $0 is the symlink path and its basename names
# the hook. This avoids per-hook shim files at the cost of one indirection.
case "$(basename "$0")" in
    post-merge)    finalize_chain_post_merge "$@" ;;
    post-commit)   finalize_chain_post_commit "$@" ;;
    post-checkout) finalize_chain_post_checkout "$@" ;;
    *)
        # Direct invocation (basename = git-finalize-hook.sh) or unknown hook
        # name. Print usage and exit cleanly — git would never invoke us this
        # way, so this only fires from a misconfigured manual run.
        echo "git-finalize-hook.sh: invoked as '$(basename "$0")'; expected" \
             "post-merge / post-commit / post-checkout. No-op." >&2
        ;;
esac
