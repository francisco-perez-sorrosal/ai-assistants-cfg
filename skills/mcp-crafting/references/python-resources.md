# Python MCP Server -- Advanced Patterns and Resources

Python-specific deep-dive content for the [mcp-crafting](../SKILL.md) skill. Load on demand.

## Table of Contents

- [Server Composition](#server-composition)
- [Deployment](#deployment)
- [Bundles -- Python-Specific](#bundles----python-specific)
- [SDK Version Guide](#sdk-version-guide)
- [Community Resources](#community-resources)

## Server Composition

### FastMCP import and mount

Two composition methods for breaking large servers into modules:

```python
from fastmcp import FastMCP

main = FastMCP("Main")
analytics = FastMCP("Analytics")

# import_server — one-time copy with prefix (static)
main.import_server(analytics, prefix="analytics")

# mount — live link with delegation (dynamic)
main.mount("analytics", analytics)
```

### Proxy Pattern

Bridge transports or aggregate remote servers behind a local entry point:

```python
from fastmcp import FastMCP, Client

proxy = FastMCP.as_proxy(Client("http://remote-server/mcp"))
```

### Multiple Servers on Starlette

```python
from starlette.applications import Starlette
from starlette.routing import Mount
from mcp.server.fastmcp import FastMCP

echo = FastMCP("Echo")
math = FastMCP("Math")

app = Starlette(routes=[
    Mount("/echo", echo.streamable_http_app()),
    Mount("/math", math.streamable_http_app()),
])
# Clients connect to /echo/mcp and /math/mcp
```

## Deployment

### Docker

```dockerfile
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
CMD ["uv", "run", "mcp", "run", "server.py"]
```

Key practices:
- Multi-stage builds for smaller images
- Multi-platform images (amd64 + arm64)
- Never hardcode API keys -- use environment variables or Docker secrets
- Set memory and CPU limits

### PyPI Distribution

Distribute as a standard Python package:

```toml
[project.scripts]
mcp-server-myproject = "mcp_server_myproject.server:main"
```

Install with `uv tool install mcp-server-myproject` or `pip install mcp-server-myproject`.

### CI/CD (GitHub Actions)

```yaml
- uses: astral-sh/setup-uv@v7
  with:
    enable-cache: true

- run: uv sync --all-extras --dev
- run: uv run pytest
- run: uv run ruff check .
- run: uv run pyright src/
```

## Bundles -- Python-Specific

### Python uv Bundle (Recommended)

```text
my-server.mcpb (ZIP)
├── manifest.json
├── pyproject.toml
├── src/
│   └── server.py
└── .mcpbignore
```

### Python Traditional Bundle

```text
my-server.mcpb (ZIP)
├── manifest.json
├── server/
│   ├── main.py
│   └── utils.py
├── lib/                  # Pre-bundled packages
└── requirements.txt
```

### Key Considerations for Python Bundles

- **`uv` type is experimental** (v0.4+) but is the only portable option for compiled dependencies
- **Traditional `python` type** cannot portably bundle compiled packages (e.g., pydantic, numpy)
- **Node.js is recommended** by the spec for widest compatibility -- it ships with Claude Desktop
- The MCP Python SDK has no built-in bundle support -- use the `@anthropic-ai/mcpb` npm CLI
- `.mcpbignore` works like `.gitignore` to exclude files from the archive

## SDK Version Guide

### Current State (early 2026)

| SDK | Version | Status |
|-----|---------|--------|
| `mcp` | v1.x | **Production recommended**. Pin `>=1.25,<2` |
| `mcp` | v2 | Pre-alpha on `main`. Expected Q1 2026 |
| `fastmcp` | v2.x | Stable standalone. Pin `<3` |
| `fastmcp` | v3.0 | Beta. New primitives (providers, transforms) |

v1.x will receive bug fixes and security updates for 6+ months after v2 ships.

### v1 vs v2 Key Differences

| Aspect | v1.x | v2 |
|--------|------|-----|
| High-level API | `FastMCP` at `mcp.server.fastmcp` | `MCPServer` at `mcp.server.mcpserver` |
| Structured output | Not built-in | Native Pydantic, TypedDict, dataclass |
| Transports | stdio, SSE | stdio, Streamable HTTP |
| Elicitation | Not available | Form mode and URL mode |

### FastMCP Standalone History

- **FastMCP 1.0** -- incorporated into the official SDK in 2024 (as `mcp.server.fastmcp`)
- **FastMCP 2.x** -- stable standalone release, extends beyond the SDK
- **FastMCP 3.0** -- beta, adds providers, transforms, hot reload, background tasks

Migration from SDK-bundled to standalone is often just changing the import:
```python
# From SDK-bundled:
from mcp.server.fastmcp import FastMCP
# To standalone:
from fastmcp import FastMCP
```

## Community Resources

### Official Python

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Build a Server Tutorial](https://modelcontextprotocol.io/docs/develop/build-server)
- [create-python-server Template](https://github.com/modelcontextprotocol/create-python-server)

### FastMCP

- [FastMCP Documentation](https://gofastmcp.com/)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [FastMCP Testing Patterns](https://gofastmcp.com/patterns/testing)
- [Stop Vibe-Testing Your MCP Server](https://www.jlowin.dev/blog/stop-vibe-testing-mcp-servers)

### Tutorials

- [Real Python: MCP Server Tutorial](https://realpython.com/python-mcp/)
- [DigitalOcean: MCP Server -- Everything I Wish I'd Known on Day One](https://www.digitalocean.com/community/tutorials/mcp-server-python)
- [Microsoft MCP for Beginners](https://github.com/microsoft/mcp-for-beginners)
- [15 Best Practices for Building MCP Servers in Production](https://thenewstack.io/15-best-practices-for-building-mcp-servers-in-production/)
