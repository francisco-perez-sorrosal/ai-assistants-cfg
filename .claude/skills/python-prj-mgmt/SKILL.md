---
name: Python Project Management
description: Python project management with pixi and uv package managers. Use when setting up Python projects, managing dependencies, configuring environments, initializing projects, or choosing between package management tools. Defaults to pixi unless uv is explicitly requested.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# Python Project Management

Managing Python projects with modern package managers and dependency tools. **Default: pixi** unless uv is explicitly requested.

## Quick Reference

**Python Coding**: See the [Python Development](../python/SKILL.md) skill for type hints, testing patterns, code quality, and language best practices.

**Package Managers**:
- [pixi](pixi.md) - **Default** - Python-native with pyproject.toml, conda+PyPI ecosystem
- [uv](uv.md) - Fast Python package installer and resolver

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

# Development dependencies
pixi add --pypi --feature dev pytest ruff mypy

# Install all dependencies
pixi install
```

### With uv

```bash
# Add dependencies
uv add requests pandas numpy

# Development dependencies
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

## Common Workflows

### Development Setup (pixi)

```bash
# Initialize
pixi init my-project --format pyproject
cd my-project

# Add dependencies
pixi add --pypi requests pandas
pixi add numpy  # conda version (better for numpy)

# Add dev tools
pixi add --pypi --feature dev pytest mypy ruff

# Run development tasks
pixi run pytest
pixi run mypy src/
pixi run ruff check .
```

### Development Setup (uv)

```bash
# Initialize
uv init my-project
cd my-project

# Set Python version
uv python pin 3.11

# Add dependencies
uv add requests pandas numpy

# Add dev tools
uv add --dev pytest mypy ruff

# Run development tasks
uv run pytest
uv run mypy src/
uv run ruff check .
```

### CI/CD Integration

#### pixi (GitHub Actions)

```yaml
- uses: prefix-dev/setup-pixi@v0.4.1
  with:
    pixi-version: latest
    cache: true

- run: pixi install
- run: pixi run pytest
- run: pixi run mypy src/
```

#### uv (GitHub Actions)

```yaml
- uses: astral-sh/setup-uv@v3
  with:
    enable-cache: true

- run: uv python install
- run: uv sync --all-extras --dev
- run: uv run pytest
- run: uv run mypy src/
```

## pyproject.toml Integration

Both pixi and uv use `pyproject.toml` as the primary configuration file, following Python standards (PEP 621, PEP 735).

### Basic pyproject.toml

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

### pixi-specific config

```toml
[tool.pixi.workspace]
channels = ["conda-forge"]
platforms = ["linux-64", "osx-64", "osx-arm64", "win-64"]

[tool.pixi.dependencies]
# Conda packages (takes precedence over PyPI)
numpy = ">=1.24"

[tool.pixi.pypi-dependencies]
# Editable install
my-project = { path = ".", editable = true }

[tool.pixi.environments]
default = { solve-group = "default" }
dev = { features = ["dev"], solve-group = "default" }

[tool.pixi.tasks]
test = "pytest tests/"
lint = "ruff check ."
format = "ruff format ."
```

### uv-specific config

```toml
[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "mypy>=1.7.0",
]

[tool.uv.sources]
# Optional: custom package sources
internal-pkg = { git = "https://github.com/org/repo" }
```

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

## Package Source Guidance (pixi)

**Use PyPI** (pixi add --pypi):
- Pure Python packages
- Latest package versions
- Packages not in conda-forge

**Use conda** (pixi add):
- System libraries (libxml2, etc.)
- C extensions (numpy, scipy, pandas)
- ML frameworks (pytorch, tensorflow)
- Complex dependencies requiring compiled binaries

**Both work together**: pixi automatically manages dependencies from both ecosystems.

## Quick Commands Reference

### pixi

```bash
# Project
pixi init --format pyproject      # Initialize Python project
pixi install                      # Install from lockfile

# Dependencies
pixi add --pypi package           # Add PyPI package
pixi add package                  # Add conda package
pixi remove package               # Remove package
pixi list                         # List packages
pixi tree                         # Dependency tree

# Running
pixi run command                  # Run in environment
pixi shell                        # Interactive shell

# Tasks
pixi task list                    # List tasks
pixi run task-name                # Run task

# Maintenance
pixi update                       # Update dependencies
pixi clean cache                  # Clean cache
```

### uv

```bash
# Project
uv init                           # Initialize project
uv sync                           # Sync dependencies

# Dependencies
uv add package                    # Add dependency
uv add --dev package             # Add dev dependency
uv remove package                # Remove package
uv tree                          # Dependency tree

# Python versions
uv python install 3.11           # Install Python version
uv python pin 3.11               # Pin version

# Running
uv run command                   # Run in environment

# Build
uv build                         # Build package
uv publish                       # Publish to PyPI

# Maintenance
uv cache clean                   # Clean cache
```

## Migration Between Tools

### From pip to pixi

```bash
pixi init --format pyproject
cat requirements.txt | xargs -n 1 pixi add --pypi
```

### From pip to uv

```bash
uv init
cat requirements.txt | xargs -n 1 uv add
```

### From poetry to pixi/uv

Both tools can read poetry's `pyproject.toml` directly.

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

## Additional Resources

- [pixi Documentation](pixi.md) - Complete pixi reference
- [uv Documentation](uv.md) - Complete uv reference
- [Python Development Skill](../python/SKILL.md) - Coding best practices
