Your task is to merge in the $ARGUMENTS worktree in the ./trees/$ARGUMENTS folder.

Follow these steps:

1. Change into the .trees/$ARGUMENTS directory
2. Examine and understand in depth the changes that were made in the last commit
3. Change back to the root directory
4. Merge in the worktree
5. There migth be merge conflicts. Use the `git status`, `git diff --name-only --diff-filter=U`, or `git ls-files -u` to list files that have merge conflicts
6. Resolve the conflicts based upon your knowledge of the changes and continue the merging process
