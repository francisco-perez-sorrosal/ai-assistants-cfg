---
description: Python project management with pixi and uv package managers. Covers project initialization, dependency management, pyproject.toml configuration, lockfiles, virtual environments, workspaces, and CI/CD integration. Use when setting up Python projects, managing dependencies, configuring conda or PyPI packages, choosing between package managers, or working with pixi.lock or uv.lock. Defaults to pixi unless uv is explicitly requested.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
compatibility: Claude Code
---

# Python Project Management

Managing Python projects with modern package managers and dependency tools. **Default: pixi** unless uv is explicitly requested.

## Quick Reference

**Python Coding**: See the [Python Development](../python-development/SKILL.md) skill for type hints, testing patterns, code quality, and language best practices.

**Package Managers**:
- [pixi](pixi.md) - **Default** - conda+PyPI ecosystem, tasks, multi-language support
- [uv](uv.md) - Extremely fast PyPI-only installer and resolver

## Default Behavior

**Use pixi** unless the user explicitly mentions uv or requests uv-specific features.

## When to Use Which

### Use pixi (Default)

- Multi-ecosystem projects (Python + system libraries)
- ML/Data science (PyTorch, TensorFlow, NumPy, SciPy)
- Projects needing conda packages
- Cross-platform reproducibility
- Projects requiring C extensions or compiled libraries
- Teams already using conda/mamba

### Use uv (When Requested)

- Pure Python projects
- Need blazing fast installs (10-100x faster than pip)
- pip/pip-tools migration
- Minimal dependencies
- Projects that don't need conda ecosystem

## Project Initialization

### With pixi (Default)

```bash
pixi init my-project --format pyproject
cd my-project

# Creates:
# - pyproject.toml (project config)
# - src/my_project/ (source package)
# - tests/ (test directory)
# - pixi.lock (lockfile)
```

### With uv

```bash
uv init my-project
cd my-project

# Creates:
# - pyproject.toml (project config)
# - README.md
# - .python-version (Python version pin)
```

## Project Structure

```
project/
├── pyproject.toml          # Project metadata, dependencies, tool configs
├── pixi.lock              # Lockfile (pixi) or uv.lock (uv)
├── README.md              # Documentation
├── src/
│   └── package_name/
│       ├── __init__.py
│       ├── module.py
│       └── py.typed      # Type checking marker
├── tests/
│   ├── __init__.py
│   ├── conftest.py       # Pytest fixtures
│   └── test_module.py
└── .gitignore
```

## Dependency Management

### With pixi

```bash
# PyPI packages (default for pure Python)
pixi add --pypi requests pandas

# Conda packages (for compiled libs, ML frameworks)
pixi add numpy scipy pytorch

# Development dependency group
pixi add --pypi --feature dev pytest ruff mypy

# Install all dependencies
pixi install
```

### With uv

```bash
# Add dependencies
uv add requests pandas numpy

# Development dependency group
uv add --dev pytest ruff mypy

# Sync dependencies
uv sync
```

## Running Commands

### With pixi

```bash
pixi run python script.py      # Run script
pixi run pytest               # Run tests
pixi run mypy src/            # Type check

# Interactive shell
pixi shell
```

### With uv

```bash
uv run python script.py       # Run script
uv run pytest                # Run tests
uv run mypy src/             # Type check

# No activation needed with uv run
```

### CI/CD Integration

#### pixi (GitHub Actions)

```yaml
- uses: prefix-dev/setup-pixi@v0.9.4
  with:
    pixi-version: latest
    cache: true

- run: pixi install
- run: pixi run pytest
- run: pixi run mypy src/
```

#### uv (GitHub Actions)

```yaml
- uses: astral-sh/setup-uv@v7
  with:
    enable-cache: true

- run: uv python install
- run: uv sync --all-extras --dev
- run: uv run pytest
- run: uv run mypy src/
```

## pyproject.toml Configuration

Both pixi and uv use `pyproject.toml` as the primary configuration file, following Python standards (PEP 621, PEP 735). The shared structure is identical; tool-specific sections differ.

### Shared pyproject.toml

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "Project description"
authors = [{ name = "Your Name", email = "email@example.com" }]
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31.0",
    "pandas>=2.0.0",
]

[dependency-groups]
dev = ["pytest>=7.4", "mypy>=1.7", "ruff>=0.1"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

For tool-specific `pyproject.toml` sections (`[tool.pixi.*]`, `[tool.uv]`), see the corresponding reference files: [pixi.md](pixi.md) and [uv.md](uv.md).

## Package Manager Comparison

| Feature | pixi | uv |
|---------|------|-----|
| **Speed** | Fast (parallel downloads) | Extremely fast (10-100x pip) |
| **Ecosystem** | conda + PyPI | PyPI only |
| **Config** | pyproject.toml | pyproject.toml |
| **Lockfile** | pixi.lock | uv.lock |
| **Python mgmt** | Via conda | Built-in (uv python) |
| **Multi-language** | Yes (R, C++, etc.) | Python only |
| **System libs** | Excellent (conda) | Limited (PyPI) |
| **ML frameworks** | Excellent | Good |
| **Pure Python** | Good | Excellent |
| **Maturity** | Mature (conda ecosystem) | New but stable |

## Command Quick Reference

For complete command references, see [pixi.md](pixi.md) and [uv.md](uv.md). The most common commands:

| Task | pixi | uv |
|------|------|-----|
| Initialize | `pixi init --format pyproject` | `uv init` |
| Add dependency | `pixi add --pypi pkg` | `uv add pkg` |
| Add conda dependency | `pixi add pkg` | N/A |
| Add dev dependency | `pixi add --pypi --feature dev pkg` | `uv add --dev pkg` |
| Install/sync | `pixi install` | `uv sync` |
| Run command | `pixi run cmd` | `uv run cmd` |
| Update lockfile | `pixi update` | `uv lock` |
| Dependency tree | `pixi tree` | `uv tree` |

## Best Practices

1. **Commit lockfiles** (`pixi.lock` or `uv.lock`) for reproducibility
2. **Use pyproject.toml** for all configuration
3. **Set Python version** explicitly in `requires-python`
4. **Organize dependencies** with dependency groups (dev, test, docs)
5. **Define tasks** for common operations (pixi)
6. **Version constraints**: Be specific for applications, flexible for libraries
7. **Keep configs clean**: Don't specify transitive dependencies

## Common Pitfalls

### pixi

- Mixing conda and PyPI sources incorrectly (use `--pypi` flag explicitly)
- Missing `--format pyproject` on init (creates pixi.toml instead)
- Not setting `system-requirements.cuda` for GPU packages
- Mixing conda-forge with legacy pytorch channel

### uv

- Not pinning Python version (use `uv python pin`)
- Forgetting to sync after adding dependencies
- Using venv activation instead of `uv run` (slower)

## Reference Files

- [pixi Reference](pixi.md) — Complete pixi guide: environments, tasks, ML workflows, troubleshooting
- [uv Reference](uv.md) — Complete uv guide: workspaces, build/publish, Python version management
