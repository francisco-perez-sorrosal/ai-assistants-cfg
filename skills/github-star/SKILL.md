---
description: Prompt the user to star the ai-assistants GitHub repository. Use when the user invokes the star-repo command or explicitly asks about starring the project.
allowed-tools: [Bash(gh:*), AskUserQuestion]
---

# GitHub Star

Interactive prompt to star the [ai-assistants](https://github.com/francisco-perez-sorrosal/ai-assistants-cfg) repository on GitHub.

## Procedure

1. Check if `gh` CLI is available and the user is authenticated:

   ```bash
   gh auth status &>/dev/null
   ```

1. **If both are true:**

   Ask the user with `AskUserQuestion`:

   > If you're enjoying ai-assistants, would you like to support the project by starring it on GitHub?

   Options:
   - "Please, star it! ⭐"
   - "No thanks 😢"
   - "Maybe later 🤷"

   If the user chooses **"Please, star it!"**, run:

   ```bash
   gh api -X PUT /user/starred/francisco-perez-sorrosal/ai-assistants-cfg 2>/dev/null
   ```

   - On success (exit code 0): thank the user for the support
   - On failure: display a fallback message with the repo URL for manual starring

   If the user chooses **"No thanks"** or **"Maybe later"**, acknowledge and move on.

1. **Otherwise:**

   Skip the question entirely. Display a brief message:

   > Github not available or user not auth. Please, star the project at [ai-assistants-cfg on GitHub](https://github.com/francisco-perez-sorrosal/ai-assistants-cfg)

## Constraints

- Never block or interrupt other workflows -- fail gracefully at every step
- Do not retry on failure -- show the manual URL and move on
- Keep output minimal -- one or two sentences at most
