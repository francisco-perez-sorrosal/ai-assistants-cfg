## Commit Message Format

```
<type>: <subject>

<body>
```

**Subject line:**

- Use imperative mood ("Add" not "Added", "Fix" not "Fixed")
- Keep under 50 characters
- No period at the end
- Be specific: "Fix null check in auth handler" not "Fix bug"

**Type prefix** (optional but recommended):

- `feat`: new feature
- `fix`: bug fix
- `refactor`: code restructuring without behavior change
- `docs`: documentation only
- `test`: adding/updating tests
- `chore`: maintenance, dependencies, config

**Body** (when changes need context):

- Separate from subject with blank line
- Wrap at 72 characters
- Explain *what* and *why*, not *how*
- Reference related issues if applicable

## Examples

Simple change:

```
fix: Handle empty input in validation
```

Change needing context:

```
feat: Add retry logic for API calls

Transient network failures were causing silent data loss.
Retry up to 3 times with exponential backoff before failing.
```

