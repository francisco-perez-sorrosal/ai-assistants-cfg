## Coding Style

Language-independent structural and design conventions for writing and reviewing code.

### Core Principles

- Object and functional programming with immutable data when possible
- Self-documenting code — readable enough that comments are rarely needed
- Comments only to clarify complex algorithms or obscure language idioms to other readers
- Natural line breaks unless the surrounding code is wrapped at a specific column
- Trailing newline in all files

### Language-Specific Style

Formatting, linting rules, and language idioms belong to each language's toolchain — not here. Delegate to the appropriate tools (e.g., `ruff`/`black` for Python, `prettier` for JS/TS, `rustfmt` for Rust, `gofmt` for Go). This rule covers structural and design conventions that transcend any single language.

### Immutability

Create new objects instead of mutating existing ones. When a language provides immutable alternatives, prefer them.

```
// Wrong — mutates in place
config["timeout"] = 30

// Right — produces a new copy with the change
new_config = copy(config, timeout = 30)
```

Rationale: immutable data prevents hidden side effects, simplifies debugging, and enables safe concurrency.

Exceptions: performance-critical inner loops where allocation cost is measured and significant, or when the language idiom strongly favors mutation (e.g., builder patterns).

### Code Organization

- Modularize with meaningful, well-scoped package/module names
- Avoid catch-all modules like `utils` — only use when a function is so generic it has no natural home
- When a module grows large, extract its helpers into `<module_name>_utils`, not a shared `utils`
- Break code into multiple files before splitting across directories

### File Size

- Target: 200–400 lines
- Hard ceiling: 800 lines — beyond this, split by cohesion
- Extract when a file covers two or more unrelated concerns, regardless of line count

### Function Size

- Target: under 30 lines of logic (excluding docstrings, blank lines, and signatures)
- Hard ceiling: 50 lines — beyond this, extract a helper
- A function should do one thing and be nameable without conjunctions ("and", "or", "then")

### Nesting Depth

- Maximum 4 levels of indentation in any function
- Use early returns, guard clauses, and extraction to flatten logic

```
// Wrong — deep nesting
function process(items):
    if items is not empty:
        for item in items:
            if item.isValid():
                if item.needsUpdate():
                    update(item)

// Right — early return + guard clause
function process(items):
    if items is empty:
        return
    for item in items:
        if not item.isValid():
            continue
        if item.needsUpdate():
            update(item)
```

### Error Handling

- Handle errors explicitly at every level — never silently swallow exceptions
- UI-facing code: user-friendly messages with actionable guidance
- Internal/server code: log full context (stack trace, input values, operation attempted)
- Distinguish recoverable errors (retry, fallback) from fatal ones (fail fast)

### Input Validation

Validate at system boundaries only — not between trusted internal modules.

System boundaries:
- User input (CLI args, form data, API request bodies)
- External API responses
- File content and environment variables
- Database query results when schema is not enforced

Use schema-based validation where available. Fail fast with clear error messages that identify what was wrong and what was expected.

### Constants Over Magic Values

- No hardcoded literals in logic — extract to named constants or configuration
- Exception: trivially obvious values (`0`, `1`, `""`, `true/false`) where meaning is self-evident in context

```
// Wrong
if retries > 3:
    sleep(0.5)

// Right
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 0.5

if retries > MAX_RETRIES:
    sleep(RETRY_DELAY_SECONDS)
```

### Naming

- Variables and functions: descriptive, intention-revealing names
- Booleans: read as yes/no questions — `is_valid`, `has_permission`, `should_retry`
- Avoid abbreviations unless universally understood (`id`, `url`, `config`)
- Collections: plural nouns (`users`, `pending_tasks`)
- Functions: verb phrases (`fetch_user`, `validate_input`, `calculate_total`)

### Code Quality Checklist

Before marking implementation complete:

- [ ] Functions are small and single-purpose
- [ ] Files are focused and within size targets
- [ ] No deep nesting (>4 levels)
- [ ] Errors are handled explicitly
- [ ] No hardcoded magic values
- [ ] Immutable patterns used where applicable
- [ ] Names are descriptive and consistent
