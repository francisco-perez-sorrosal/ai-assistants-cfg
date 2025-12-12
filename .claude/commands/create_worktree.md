Your task is to create a new worktree named .trees/$ARGUMENTS folder.

Follow these steps:

1. Check if an existing folder in the .trees folder with the name $ARGUMENTS already exists. If it
does, stoe here and tell the user that the worktree already exists
2. Create a new git worktree in the .trees folder witht he name $ARGUMENTS
3. Symlink the .venv folder into the worktree directory
4. Launches a new Cursor editor instance in that directory by running the `cursor` command
