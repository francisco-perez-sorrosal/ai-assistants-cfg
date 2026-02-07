---
description: Modern Python development conventions covering type hints, testing with pytest, code quality tools (ruff, mypy, pyright), data modeling (dataclasses, Pydantic), async patterns, and error handling. Use when writing Python code, implementing tests, configuring linting or formatting, choosing between dataclasses and Pydantic, working with structural pattern matching, or setting up pytest fixtures and parametrize.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# Modern Python Development

Comprehensive guidance for Python development following pragmatic, production-ready practices.

## Core Principles

**Pragmatic Python**: Write code that is clear, maintainable, and purposeful. Every line should have a reason to exist.

**Type Safety**: Use type hints throughout. They serve as inline documentation and catch errors early.

**Testing**: Test critical paths and edge cases. Use pytest with clear test names that describe behavior.

**Code Quality**: Maintain consistency with automated tools. Let tools handle formatting.

**Project Management**: Commands in this skill use `<tool>` as a placeholder for your project management tool (pixi or uv). See the [Python Project Management](../python-prj-mgmt/SKILL.md) skill for environment setup, dependency management, and choosing between pixi (default) and uv.

## Python Version Guidelines

**Target Python 3.13+** for new projects:
- Better error messages
- Faster performance
- Modern type hint syntax (`X | Y`, `Self`)
- Exception groups

**For libraries**, support Python 3.10+ unless specific constraints require older versions.

## Project Structure

```
project/
├── pyproject.toml          # Project metadata and dependencies
├── README.md              # Project documentation
├── src/
│   └── package_name/
│       ├── __init__.py
│       ├── module.py
│       └── py.typed      # Marker for type checking
├── tests/
│   ├── __init__.py
│   ├── conftest.py       # Pytest fixtures
│   └── test_module.py
└── .gitignore
```

## Type Hints

**Always use type hints** for function signatures and class attributes:

```python
from collections.abc import Sequence
from typing import Protocol

def process_items(items: Sequence[str], *, limit: int = 10) -> list[str]:
    """Process items with an optional limit."""
    return list(items[:limit])

class Processor(Protocol):
    """Protocol for processors."""
    def process(self, data: str) -> str: ...
```

**Modern type hint patterns** (Python 3.10+):
- Use `list[T]`, `dict[K, V]`, `set[T]` instead of `List`, `Dict`, `Set`
- Use `X | Y` instead of `Union[X, Y]`
- Use `X | None` instead of `Optional[X]`
- Use `collections.abc` types for function parameters (more flexible)

**Type checking**: Use mypy or pyright:
```bash
<tool> run mypy src/
<tool> run pyright src/
```

## Code Style

**Formatter**: Use ruff for formatting and linting:

```toml
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "A", "C4", "PT"]
ignore = ["E501"]  # Line length handled by formatter

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

## Testing with pytest

**Test structure**:
```python
import pytest
from package_name.module import process_items

def test_process_items_returns_limited_results():
    items = ["a", "b", "c", "d", "e"]
    result = process_items(items, limit=3)
    assert result == ["a", "b", "c"]

def test_process_items_handles_empty_input():
    assert process_items([]) == []

@pytest.fixture
def sample_data():
    return ["item1", "item2", "item3"]

def test_with_fixture(sample_data):
    result = process_items(sample_data, limit=2)
    assert len(result) == 2
```

**Running tests**:
```bash
<tool> run pytest                    # Run all tests
<tool> run pytest tests/test_module.py  # Specific file
<tool> run pytest -v                 # Verbose
<tool> run pytest --cov=src         # With coverage
<tool> run pytest -k "test_name"    # Filter by name
```

**Test organization**:
- One test file per module: `test_module.py` for `module.py`
- Test names should describe behavior: `test_function_handles_edge_case`
- Use fixtures for shared setup
- Use parametrize for multiple similar tests

```python
@pytest.mark.parametrize("input_val,expected", [
    ([], []),
    (["a"], ["a"]),
    (["a", "b", "c"], ["a", "b"]),
])
def test_process_items_with_various_inputs(input_val, expected):
    assert process_items(input_val, limit=2) == expected
```

## Common Patterns

**Dataclasses** for simple data containers:
```python
from dataclasses import dataclass

@dataclass(frozen=True)  # Immutable
class Config:
    host: str
    port: int
    debug: bool = False
```

**Pydantic models** for data validation and parsing:
```python
from pydantic import BaseModel, Field, ConfigDict, field_validator

class UserInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    email: str
    age: int = Field(ge=0, le=150)
    username: str = Field(min_length=3, max_length=50)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email address")
        return v.lower()

# Automatic validation on instantiation
user = UserInput(email="USER@EXAMPLE.COM", age=25, username="john")
# user.email == "user@example.com"
```

**Dataclasses vs Pydantic: When to use each**

Use **dataclasses** when:
- Simple data containers with no validation needs
- Internal data structures within your codebase
- Performance-critical paths (dataclasses have less overhead)
- No need for JSON/dict serialization/deserialization
- Working with pure Python without external dependencies

Use **Pydantic** when:
- Parsing external input (API requests, config files, user input)
- Complex validation rules are required
- Need automatic type coercion (e.g., `"123"` → `123`)
- Serialization to/from JSON or dicts is frequent
- Working with settings/configuration management
- Building APIs (FastAPI integration)

```python
# Example: Combining both approaches
from dataclasses import dataclass
from pydantic import BaseModel

# Pydantic for external input validation
class CreateUserRequest(BaseModel):
    email: str
    username: str
    age: int

# Dataclass for internal domain model
@dataclass(frozen=True)
class User:
    id: int
    email: str
    username: str
    age: int

    @classmethod
    def from_request(cls, user_id: int, request: CreateUserRequest) -> "User":
        return cls(
            id=user_id,
            email=request.email,
            username=request.username,
            age=request.age,
        )
```

**Protocols** for structural typing:
```python
from typing import Protocol

class Serializable(Protocol):
    def to_json(self) -> str: ...

def save(obj: Serializable) -> None:
    data = obj.to_json()
    # ... save data
```

**Context managers** for resource management:
```python
from contextlib import contextmanager
from typing import Iterator

@contextmanager
def managed_resource(name: str) -> Iterator[Resource]:
    resource = acquire_resource(name)
    try:
        yield resource
    finally:
        resource.cleanup()
```

**Structural pattern matching** (Python 3.10+):
```python
from dataclasses import dataclass

@dataclass
class Command:
    action: str
    name: str = ""

def handle_command(command: Command) -> str:
    match command:
        case Command(action="quit"):
            return "Goodbye"
        case Command(action="greet", name=name):
            return f"Hello, {name}"
        case _:
            return "Unknown command"
```

## Async Patterns

**Basic async/await**:
```python
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx

async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

**Async context managers** for resource lifecycle:
```python
@asynccontextmanager
async def managed_connection(url: str) -> AsyncIterator[Connection]:
    conn = await connect(url)
    try:
        yield conn
    finally:
        await conn.close()
```

**Testing**: Use `pytest-asyncio` for async test functions:
```python
import pytest

@pytest.mark.asyncio
async def test_fetch_data():
    result = await fetch_data("https://api.example.com/data")
    assert "id" in result
```

**Common async libraries**: `asyncio` (stdlib), `httpx` (async HTTP client), `aiohttp` (HTTP client/server), `anyio` (structured concurrency).

## Code Quality Tools

**Essential tools** in `pyproject.toml`:
```toml
[project]
requires-python = ">=3.11"

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-ra -q --strict-markers"

[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

**Pre-commit hooks** (optional but recommended):
```yaml
# .pre-commit-config.yaml
# Pin rev to the latest stable release — find current versions at each repo's releases page.
# Specific versions are not pinned here to avoid staleness; the pattern matters, not the pin.
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: <version>  # https://github.com/astral-sh/ruff-pre-commit/releases
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: <version>  # https://github.com/pre-commit/mirrors-mypy/tags
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

## Error Handling

**Be explicit** about error conditions:
```python
class InvalidConfigError(ValueError):
    """Raised when configuration is invalid."""
    pass

def load_config(path: str) -> Config:
    if not Path(path).exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    try:
        data = parse_config_file(path)
    except ParseError as e:
        raise InvalidConfigError(f"Invalid config format: {e}") from e

    return Config(**data)
```

## Development Workflow

1. **Initialize project** (see [Python Project Management](../python-prj-mgmt/SKILL.md))
2. **Set up tools**: ruff, mypy/pyright, pytest
3. **Write tests first** for critical functionality
4. **Implement** with type hints
5. **Run checks**: `<tool> run ruff check . && <tool> run mypy src/ && <tool> run pytest`
6. **Iterate** in small increments

## Quick Commands

For package management commands, see the [Python Project Management](../python-prj-mgmt/SKILL.md) skill.

```bash
# Code quality
<tool> run ruff check .             # Lint
<tool> run ruff format .            # Format
<tool> run mypy src/                # Type check

# Testing
<tool> run pytest                   # Run tests
<tool> run pytest --cov             # With coverage
<tool> run pytest -x                # Stop on first failure
<tool> run pytest --lf              # Run last failed
```

