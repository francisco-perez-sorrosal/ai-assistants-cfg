---
name: mcp-server
description: Building MCP (Model Context Protocol) servers in Python using the official SDK and FastMCP. Covers tools, resources, prompts, transports (stdio, streamable HTTP), bundles (.mcpb), testing with pytest and MCP Inspector, deployment, Claude Desktop/Code integration, logging, and error handling. Use when creating MCP servers, defining tools or resources, configuring MCP transports, packaging MCP bundles, testing MCP servers, or integrating with Claude Desktop or Claude Code.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# MCP Server Development in Python

Build [Model Context Protocol](https://modelcontextprotocol.io) servers that expose tools, resources, and prompts to LLM applications.

**Python Coding**: See the [Python Development](../python/SKILL.md) skill for type hints, testing patterns, code quality, and language best practices.

**Project Setup**: See the [Python Project Management](../python-prj-mgmt/SKILL.md) skill for environment setup and dependency management. The MCP SDK recommends **uv** for project management.

## SDK Landscape

Two options for building MCP servers in Python:

| Option | Package | When to Use |
|--------|---------|-------------|
| **Official SDK** | `mcp[cli]` | Default choice. Bundled FastMCP at `mcp.server.fastmcp` |
| **FastMCP standalone** | `fastmcp` | Need composition, proxying, or advanced features beyond the SDK |

**Version pinning** (production):
```toml
# Official SDK v1.x (recommended for production)
dependencies = ["mcp[cli]>=1.25,<2"]

# FastMCP standalone v2 (stable)
dependencies = ["fastmcp<3"]
```

The SDK requires **Python 3.10+**. Target **3.13+** for new projects.

## Quickstart

```bash
uv init --package mcp-server-demo
cd mcp-server-demo
uv add "mcp[cli]"
```

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Demo")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting."""
    return f"Hello, {name}!"

@mcp.prompt()
def review_code(code: str, language: str = "python") -> str:
    """Generate a code review prompt."""
    return f"Please review this {language} code:\n\n```{language}\n{code}\n```"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

Run and test:
```bash
uv run mcp dev src/server.py          # Inspector at localhost:6274
uv run mcp run src/server.py          # Direct execution (stdio)
```

## Core Primitives

### Tools — Executable Functions

Tools perform computation and side effects. The LLM invokes them.

```python
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

mcp = FastMCP("Tools Example")

@mcp.tool()
def search_database(query: str, limit: int = 10) -> list[dict]:
    """Search the database with a query string."""
    return db.execute(query, limit=limit)

@mcp.tool()
async def long_task(name: str, ctx: Context[ServerSession, None], steps: int = 5) -> str:
    """Task with progress reporting."""
    for i in range(steps):
        await ctx.report_progress(progress=(i + 1) / steps, total=1.0)
        await ctx.info(f"Step {i + 1}/{steps}")
    return f"Task '{name}' completed"
```

**Structured output** — return Pydantic models, TypedDicts, or dataclasses for typed results:

```python
from pydantic import BaseModel, Field

class WeatherData(BaseModel):
    temperature: float = Field(description="Temperature in Celsius")
    humidity: float = Field(description="Humidity percentage")
    condition: str

@mcp.tool()
def get_weather(city: str) -> WeatherData:
    """Get weather for a city."""
    return WeatherData(temperature=22.5, humidity=45.0, condition="sunny")
```

### Resources — Data Exposure

Resources provide data to LLMs (like GET endpoints). No significant side effects.

```python
@mcp.resource("config://settings")
def get_settings() -> str:
    """Application settings."""
    return '{"theme": "dark", "debug": false}'

@mcp.resource("file://docs/{path}")
def read_doc(path: str) -> str:
    """Read a document by path."""
    return Path(f"docs/{path}").read_text()
```

### Prompts — Reusable Templates

Prompts define structured interaction patterns for LLMs.

```python
@mcp.prompt()
def analyze_data(dataset: str, focus: str = "trends") -> str:
    """Generate a data analysis prompt."""
    return f"Analyze the '{dataset}' dataset, focusing on {focus}."
```

## Transports

| Transport | Use Case | Command |
|-----------|----------|---------|
| **stdio** | Local development, Claude Desktop | `mcp.run()` (default) |
| **Streamable HTTP** | Production, remote clients | `mcp.run(transport="streamable-http")` |

**SSE is deprecated.** Use streamable HTTP for all new HTTP-based servers.

### Mounting on Starlette (Multiple Servers)

```python
from starlette.applications import Starlette
from starlette.routing import Mount

app = Starlette(routes=[
    Mount("/api", api_mcp.streamable_http_app()),
    Mount("/admin", admin_mcp.streamable_http_app()),
])
```

## Lifespan — Startup/Shutdown Resources

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

@dataclass
class AppContext:
    db: Database

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    db = await Database.connect()
    try:
        yield AppContext(db=db)
    finally:
        await db.disconnect()

mcp = FastMCP("My App", lifespan=app_lifespan)

@mcp.tool()
def query(ctx: Context[ServerSession, AppContext]) -> str:
    """Query using the shared database connection."""
    return ctx.request_context.lifespan_context.db.query()
```

## Logging — Never Print to Stdout

For **stdio servers**, `print()` corrupts JSON-RPC messages. Always log to stderr:

```python
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)
```

For HTTP servers, standard output logging is fine.

## Testing

### pytest with In-Memory Client (Primary)

Test tools directly without subprocess overhead:

```python
import pytest
from mcp.server.fastmcp import FastMCP

@pytest.fixture
async def client():
    from fastmcp import Client  # or test with call_tool directly
    async with Client(mcp) as c:
        yield c

@pytest.mark.asyncio
async def test_add_tool(client):
    result = await client.call_tool("add", {"a": 2, "b": 3})
    assert result[0].text == "5"
```

Add to `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### MCP Inspector (Interactive)

```bash
uv run mcp dev src/server.py                    # Bundled Inspector
npx -y @modelcontextprotocol/inspector          # Standalone Inspector
```

## Client Integration

### Claude Desktop

**Automatic:**
```bash
uv run mcp install src/server.py --name "My Server"
```

**Manual** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):
```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/server", "mcp", "run", "server.py"]
    }
  }
}
```

### Claude Code

```bash
# HTTP server
claude mcp add --transport http my-server http://localhost:8000/mcp

# stdio server
claude mcp add my-server -- uv run /path/to/server.py

# Scope: user (all projects), local (default, this project), project (.mcp.json, shareable)
claude mcp add my-server --scope project -- uv run server.py
```

## Error Handling

- Validate inputs early — check types, ranges, required fields before processing
- Catch specific exceptions with targeted responses, fall back to generic handlers
- Return `isError: true` in `CallToolResult` for tool-level failures
- Log full error details to stderr; sanitize responses to avoid leaking internals
- Provide context-aware messages that help the LLM recover ("column 'xyz' not found — did you mean 'xy'?")

## Project Structure

```
mcp-server-myproject/
├── pyproject.toml
├── README.md
├── src/
│   └── mcp_server_myproject/
│       ├── __init__.py
│       ├── server.py          # FastMCP instance + primitives
│       └── py.typed
└── tests/
    ├── conftest.py
    └── test_server.py
```

**pyproject.toml essentials:**
```toml
[project]
name = "mcp-server-myproject"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["mcp[cli]>=1.25,<2"]

[project.scripts]
mcp-server-myproject = "mcp_server_myproject.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = ["pytest>=8.0", "pytest-asyncio>=0.24", "ruff>=0.7", "pyright>=1.1"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

## CLI Quick Reference

```bash
uv run mcp dev server.py             # Dev mode with Inspector
uv run mcp run server.py             # Run directly (stdio)
uv run mcp install server.py         # Register with Claude Desktop
```

## Bundles (`.mcpb`) — Packaging for Distribution

MCP Bundles are ZIP archives (`.mcpb` extension) containing a server and a `manifest.json`. They enable one-click installation in Claude Desktop (double-click, drag-and-drop, or Developer menu). Formerly called DXT (Desktop Extensions).

**Repository**: [modelcontextprotocol/mcpb](https://github.com/modelcontextprotocol/mcpb)

### Python Bundle (uv runtime — recommended)

```text
my-server.mcpb (ZIP)
├── manifest.json
├── pyproject.toml        # Dependencies declared here
└── src/
    └── server.py
```

**manifest.json:**

```json
{
  "manifest_version": "0.4",
  "name": "my-mcp-server",
  "version": "1.0.0",
  "description": "My MCP server",
  "author": { "name": "Your Name" },
  "server": {
    "type": "uv",
    "entry_point": "src/server.py"
  }
}
```

The `uv` server type lets the host manage Python and dependencies automatically — no need to bundle packages. For compiled dependencies, this is the only portable Python option.

### CLI

```bash
npm install -g @anthropic-ai/mcpb
mcpb init                   # Generate manifest.json interactively
mcpb pack                   # Package into .mcpb file
mcpb pack examples/hello-world-uv  # Pack a specific directory
```

### Server Types

| Type     | When to Use                                                            |
| -------- | ---------------------------------------------------------------------- |
| `node`   | **Recommended** — ships with Claude Desktop, zero install friction     |
| `uv`     | Python servers — host manages Python/deps via uv (experimental)        |
| `python` | Python with pre-bundled deps — limited portability for compiled pkgs   |
| `binary` | Pre-compiled executables                                               |

### User Configuration

Declare config fields and Claude Desktop auto-generates a settings UI:

```json
{
  "user_config": {
    "api_key": {
      "type": "string",
      "title": "API Key",
      "required": true,
      "sensitive": true
    }
  }
}
```

Reference via `${user_config.api_key}` in `mcp_config.env`.

See [references/resources.md](references/resources.md) for the full manifest specification and examples.

## Common Pitfalls

- **Printing to stdout** in stdio servers — corrupts JSON-RPC. Use `logging` to stderr
- **Using SSE transport** — deprecated. Use streamable HTTP
- **Missing type hints** — LLMs cannot understand tool parameters without annotations
- **Mixing primitives** — tools execute logic (side effects OK), resources expose data (no side effects)
- **Overly broad permissions** — start read-only, whitelist operations, restrict filesystem paths
- **Not testing** — use pytest with in-memory clients, not manual chat testing

## Related Skills

- [`python`](../python/SKILL.md) — Type hints, testing, code quality, language patterns
- [`python-prj-mgmt`](../python-prj-mgmt/SKILL.md) — uv/pixi setup, dependency management, environment configuration

## Resources

- [MCP Specification](https://modelcontextprotocol.io/specification/2025-06-18) — Official protocol spec
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) — Official SDK repository
- [FastMCP](https://gofastmcp.com/) — Standalone framework documentation
- [Build a Server Tutorial](https://modelcontextprotocol.io/docs/develop/build-server) — Official quickstart
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector) — Interactive testing tool
- [Security Best Practices](https://modelcontextprotocol.io/specification/draft/basic/security_best_practices) — Official security guidance
- See [references/resources.md](references/resources.md) for advanced patterns, deployment, and community guides
