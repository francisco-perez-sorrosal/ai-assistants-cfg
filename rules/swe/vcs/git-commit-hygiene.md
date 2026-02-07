## Git Commit Hygiene

### Commit Scope

- One logical change per commit — avoid mixing unrelated changes
- Prefer small, focused commits over large sweeping ones
- Separate refactoring from behavior changes into distinct commits

### Staging Discipline

- Stage specific files by name — avoid `git add -A` or `git add .`
- Review `git diff --staged` before every commit
- Verify the staged diff matches intent — no accidental inclusions

### Secrets and Sensitive Files

- Never commit secrets, credentials, API keys, or tokens
- Never commit `.env`, `credentials.json`, or similar config with secrets
- If a secret is accidentally staged, unstage it immediately — do not proceed with the commit
- When in doubt about whether a file contains sensitive data, err on the side of exclusion

### What Not to Commit

- Generated files (build artifacts, compiled output, lock files not meant to be tracked)
- Large binaries or media files unless the project explicitly tracks them
- Debug print statements or temporary logging left from investigation
- Commented-out code blocks — delete dead code, don't preserve it in comments

### [CUSTOMIZE] Protected Files
<!-- List files and patterns that must never be committed or require extra review:
- Environment files beyond .env (e.g., .env.local, config/secrets.yml)
- Infrastructure credentials or service account keys
- Files that should only change through a specific process (e.g., CI config, deploy scripts)
-->

### [CUSTOMIZE] Tracked Generated Files
<!-- List generated or lock files that this project intentionally tracks:
- Lock files: pixi.lock, uv.lock, package-lock.json, Cargo.lock
- Generated API clients or schema files
- Rationale for tracking each (reproducibility, CI, etc.)
-->
