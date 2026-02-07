# Rule Reference

Extended examples and migration patterns. Loaded on-demand from `SKILL.md`.

## Contents

- [Complete Rule Examples](#complete-rule-examples) -- minimal, domain-scoped, and security rules
- [Path-Specific Rule Examples](#path-specific-rule-examples) -- targeted loading with glob patterns
- [Customization Section Examples](#customization-section-examples) -- `[CUSTOMIZE]` marker patterns for project-specific content
- [Layered Directory Examples](#layered-directory-examples) -- common/ + language/ structure
- [Migration Patterns](#migration-patterns) -- moving content between layers

## Complete Rule Examples

### Minimal Rule

```markdown
## Git Commit Rules

- One logical change per commit
- Never commit secrets, credentials, or `.env` files
- Verify the diff matches intent before committing
```

### Domain-Scoped Rule

```markdown
## SQL Conventions

### Naming
- Tables: plural `snake_case` (`user_accounts`, not `UserAccount`)
- Columns: singular `snake_case` (`created_at`, not `CreatedAt`)
- Indexes: `idx_<table>_<columns>` (`idx_orders_customer_id`)

### Queries
- No `SELECT *` — enumerate columns explicitly
- Explicit `JOIN` syntax only (no comma-separated tables)
- Always alias tables in multi-table queries
- Use CTEs over nested subqueries for readability

### Migrations
- Every migration must be reversible
- Never drop columns in production without a deprecation period
- Add indexes concurrently when possible (`CREATE INDEX CONCURRENTLY`)
```

### Security Rule

```markdown
## Auth Token Handling

- Never log tokens, API keys, or session identifiers
- Tokens must be stored in httpOnly, secure cookies — never localStorage
- Validate token expiry server-side on every request
- Rotate refresh tokens on each use (one-time use pattern)
- Revoke all tokens on password change

### Error Responses
- Auth failures return generic "unauthorized" — never reveal whether user exists
- Rate-limit auth endpoints (5 attempts per minute per IP)
```

## Path-Specific Rule Examples

### TypeScript API Files

```markdown
---
paths:
  - "src/api/**/*.ts"
  - "src/api/**/*.tsx"
---

## API Conventions

- All handlers use the `ApiHandler` type from `src/lib/types.ts`
- Return structured `{ data, error, status }` responses
- Validate request body with zod schemas before processing
- Log request ID on entry and exit for traceability
```

### Test Files

```markdown
---
paths:
  - "tests/**"
  - "**/*.test.*"
  - "**/*.spec.*"
---

## Testing Conventions

- Use `describe` blocks grouped by function/method under test
- Test names follow "should <expected behavior> when <condition>" pattern
- No shared mutable state between tests
- Prefer factory functions over fixtures for test data
```

## Customization Section Examples

### Rule with Customization Sections

A coding-style rule that separates universal conventions from project-specific content:

```markdown
## Coding Style

### Naming
- Variables: descriptive, intention-revealing names
- Booleans: read as yes/no questions — `is_valid`, `has_permission`
- Collections: plural nouns — `users`, `pending_tasks`
- Functions: verb phrases — `fetch_user`, `validate_input`

### Error Handling
- Handle errors explicitly — never silently swallow exceptions
- Distinguish recoverable errors (retry, fallback) from fatal ones (fail fast)
- Log full context: stack trace, input values, operation attempted

### [CUSTOMIZE] Project Naming Conventions
<!-- Add project-specific naming patterns here:
- Prefix conventions for modules/packages
- Domain-specific naming (e.g., database models, API routes)
- Abbreviations accepted in this codebase
-->

### [CUSTOMIZE] Error Reporting
<!-- Add project-specific error reporting here:
- Error tracking service (Sentry, Datadog, etc.)
- Alert thresholds and escalation rules
- Required error metadata fields
-->
```

### Minimal Rule with Optional Customization

A testing rule where customization is optional — the universal conventions stand alone:

```markdown
---
paths:
  - "tests/**"
  - "**/*.test.*"
  - "**/*.spec.*"
---

## Testing Conventions

- Use `describe` blocks grouped by function/method under test
- Test names follow "should <expected behavior> when <condition>" pattern
- No shared mutable state between tests
- Prefer factory functions over fixtures for test data

### [CUSTOMIZE] Test Infrastructure
<!-- Optional — add if your project has specific test infrastructure:
- Custom test utilities or helpers location
- Required test database setup
- CI-specific test configuration
-->
```

### Glob Pattern Reference

```markdown
# Common patterns for `paths` frontmatter:

"**/*.ts"                 # All TypeScript files recursively
"src/api/**"              # Everything under src/api/
"*.{ts,tsx}"              # Brace expansion — .ts and .tsx at root
"src/**/*.{js,jsx,ts,tsx}" # All JS/TS files under src/
"tests/"                  # All files under tests/ directory
"!**/node_modules/**"     # Negation — exclude node_modules
```

## Layered Directory Examples

### Full Structure

```
.claude/rules/
├── common/
│   ├── coding-style.md       # Universal formatting, naming
│   ├── testing.md             # Cross-language test principles
│   └── security.md            # Security baseline for all code
├── typescript/
│   ├── coding-style.md        # TS-specific: strict mode, type patterns
│   └── testing.md             # Jest/Vitest conventions
└── python/
    ├── coding-style.md        # Python-specific: type hints, ruff config
    └── testing.md             # pytest conventions, fixtures
```

### Extension Pattern

`typescript/coding-style.md`:
```markdown
## TypeScript Coding Style

This extends `common/coding-style.md` with TypeScript-specific conventions.

- Enable `strict` mode in all `tsconfig.json` files
- Prefer `interface` over `type` for object shapes (unless union/intersection needed)
- Use `readonly` for properties that shouldn't change after construction
- Avoid `any` — use `unknown` and narrow with type guards
- Barrel exports (`index.ts`) only at package boundaries, not within packages
```

`python/coding-style.md`:
```markdown
## Python Coding Style

This extends `common/coding-style.md` with Python-specific conventions.

- Type hints on all public functions and methods
- Use `ruff` for linting and formatting (replaces black, isort, flake8)
- Prefer `dataclass` for simple data containers, `Pydantic` for validation
- Use `pathlib.Path` over `os.path` for all path operations
- f-strings over `.format()` or `%` formatting
```

## Migration Patterns

### CLAUDE.md to Rule

**When**: A section in `CLAUDE.md` is context-specific and verbose.

Before (`CLAUDE.md`):
```markdown
## SQL Conventions
- Always use snake_case for column names
- No SELECT * — enumerate columns
- Explicit JOIN syntax only
- Foreign keys must be indexed
- Use CTEs over subqueries
- Migrations must be reversible
...20 more lines
```

After — move to `.claude/rules/sql.md` and leave a brief directive in `CLAUDE.md`:
```markdown
## SQL
- Follow SQL conventions (loaded automatically via rules)
```

### Rule to Skill

**When**: A rule keeps growing procedural content (step-by-step workflows, creation guides).

Sign the content is a skill, not a rule:
- "First do X, then do Y, then check Z"
- Includes tool invocations or bash commands
- Describes a workflow, not constraints

Move the procedural parts to a `skills/<domain>/SKILL.md` and keep only the declarative constraints in the rule.

### Consolidating Fragmented Rules

**When**: Multiple small files always load together and cover the same domain.

Before:
```
.claude/rules/
├── sql-naming.md        # 5 lines
├── sql-queries.md       # 8 lines
└── sql-migrations.md    # 6 lines
```

After — merge into `.claude/rules/sql.md` with sections:
```markdown
## SQL Conventions

### Naming
...

### Queries
...

### Migrations
...
```
