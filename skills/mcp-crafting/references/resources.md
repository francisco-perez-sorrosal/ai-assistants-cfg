# MCP Server — Advanced Patterns and Resources

Deep-dive content for the [mcp-crafting](../SKILL.md) skill. Load on demand.

## Table of Contents

- [Bundles (.mcpb)](#bundles-mcpb)
- [Server Composition](#server-composition)
- [Security](#security)
- [Deployment](#deployment)
- [SDK Version Guide](#sdk-version-guide)
- [FastMCP Standalone](#fastmcp-standalone)
- [Community Resources](#community-resources)

## Bundles (.mcpb)

MCP Bundles (`.mcpb`) are ZIP archives for distributing MCP servers as installable packages. Formerly called DXT (Desktop Extensions). Users install by double-clicking, dragging into Claude Desktop, or via Developer > Extensions > Install Extension.

**Repository**: [modelcontextprotocol/mcpb](https://github.com/modelcontextprotocol/mcpb)

### Manifest Specification (v0.4)

Full spec: [MANIFEST.md](https://github.com/modelcontextprotocol/mcpb/blob/main/MANIFEST.md)

**Required fields:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `manifest_version` | string | `"0.3"` or `"0.4"` |
| `name` | string | Machine-readable identifier |
| `version` | string | Semver (e.g., `"1.0.0"`) |
| `description` | string | Brief explanation |
| `author` | object | `{ "name": "...", "email": "...", "url": "..." }` (name required) |
| `server` | object | Runtime configuration |

**Optional fields:** `display_name`, `long_description`, `icon`/`icons`, `repository`, `homepage`, `documentation`, `support`, `screenshots`, `tools`, `tools_generated`, `prompts`, `prompts_generated`, `keywords`, `license`, `privacy_policies`, `compatibility`, `user_config`, `localization`, `_meta`.

### Complete Python Manifest Example

```json
{
  "manifest_version": "0.4",
  "name": "my-analytics-server",
  "version": "1.0.0",
  "display_name": "Analytics Server",
  "description": "Query analytics data from your dashboard",
  "author": {
    "name": "Your Name",
    "email": "you@example.com",
    "url": "https://example.com"
  },
  "server": {
    "type": "uv",
    "entry_point": "src/server.py"
  },
  "user_config": {
    "api_key": {
      "type": "string",
      "title": "API Key",
      "description": "Your analytics API key",
      "required": true,
      "sensitive": true
    },
    "base_url": {
      "type": "string",
      "title": "Base URL",
      "description": "Analytics endpoint URL",
      "required": false,
      "default": "https://api.analytics.example.com"
    }
  },
  "tools": [
    {
      "name": "query_metrics",
      "description": "Query metrics from the analytics dashboard"
    }
  ],
  "compatibility": {
    "platforms": ["darwin", "win32", "linux"],
    "runtimes": {
      "python": ">=3.11"
    }
  },
  "keywords": ["analytics", "metrics", "dashboard"],
  "license": "MIT"
}
```

### Variable Substitution in `mcp_config`

For `python` type (traditional), use `mcp_config` with variable substitution:

```json
{
  "server": {
    "type": "python",
    "entry_point": "server/main.py",
    "mcp_config": {
      "command": "python3",
      "args": ["${__dirname}/server/main.py"],
      "env": {
        "PYTHONPATH": "${__dirname}/lib",
        "API_KEY": "${user_config.api_key}"
      }
    }
  }
}
```

Available variables: `${__dirname}` (bundle root), `${user_config.KEY}` (user settings), `${HOME}`, `${locale}`.

### Bundle Directory Structures

**Python uv bundle (recommended):**

```text
my-server.mcpb (ZIP)
├── manifest.json
├── pyproject.toml
├── src/
│   └── server.py
└── .mcpbignore
```

**Python traditional bundle:**

```text
my-server.mcpb (ZIP)
├── manifest.json
├── server/
│   ├── main.py
│   └── utils.py
├── lib/                  # Pre-bundled packages
└── requirements.txt
```

**Node.js bundle (zero-install friction — recommended for widest reach):**

```text
my-server.mcpb (ZIP)
├── manifest.json
├── server/
│   └── index.js
├── node_modules/
└── package.json
```

### Key Considerations for Python Bundles

- **`uv` type is experimental** (v0.4+) but is the only portable option for compiled dependencies
- **Traditional `python` type** cannot portably bundle compiled packages (e.g., pydantic, numpy)
- **Node.js is recommended** by the spec for widest compatibility — it ships with Claude Desktop
- The MCP Python SDK has no built-in bundle support — use the `@anthropic-ai/mcpb` npm CLI
- `.mcpbignore` works like `.gitignore` to exclude files from the archive

### Official Examples

See [mcpb/examples](https://github.com/modelcontextprotocol/mcpb/tree/main/examples) for `hello-world-node`, `hello-world-uv`, `file-manager-python`, and more.

### Bundle Resources

- [Adopting the MCP Bundle Format](http://blog.modelcontextprotocol.io/posts/2025-11-20-adopting-mcpb/) — MCP Blog announcement
- [Building Desktop Extensions with MCPB](https://support.claude.com/en/articles/12922929-building-desktop-extensions-with-mcpb) — Claude Help Center
- [Desktop Extensions](https://www.anthropic.com/engineering/desktop-extensions) — Anthropic Engineering blog
- [@anthropic-ai/mcpb](https://www.npmjs.com/package/@anthropic-ai/mcpb) — npm CLI package

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

## Security

### The Lethal Trifecta (Simon Willison)

Three conditions that combine to create extreme risk:

1. **Access to private data** — the server reads sensitive information
2. **Exposure to malicious instructions** — prompt injection via untrusted content
3. **Ability to exfiltrate** — the server can send data externally

When all three are present, a prompt injection attack can steal data through the tool.

### Known Attack Vectors

- **Rug Pull / Silent Redefinition** — MCP tools can mutate their own definitions post-installation
- **Cross-Server Tool Shadowing** — a malicious server overrides calls to trusted servers
- **Tool Poisoning** — malicious instructions embedded in tool descriptions (visible to LLM, not users)

### Mitigations

- Alert users on tool description changes
- Keep humans in the loop for tool invocations
- Use OAuth with scoped, time-limited tokens
- Start read-only — whitelist operations, restrict filesystem paths
- Parameterize queries — never build commands from raw LLM output
- Taint tracking: block or require approval when tainted state reaches exfiltration-capable actions

See the [official security guidance](https://modelcontextprotocol.io/specification/draft/basic/security_best_practices).

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
- Never hardcode API keys — use environment variables or Docker secrets
- Set memory and CPU limits

### PyPI Distribution

Distribute as a standard Python package:

```toml
[project.scripts]
mcp-server-myproject = "mcp_server_myproject.server:main"
```

Install with `uv tool install mcp-server-myproject` or `pip install mcp-server-myproject`.

### Claude Code `.mcp.json` (Team Sharing)

Commit to the project root for team-wide server configuration:

```json
{
  "mcpServers": {
    "my-tool": {
      "command": "uv",
      "args": ["run", "server.py"],
      "env": {
        "API_KEY": ""
      }
    }
  }
}
```

Team members approve on first use. Scope levels: `local` (default, private), `project` (`.mcp.json`, shareable), `user` (all projects).

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

- **FastMCP 1.0** — incorporated into the official SDK in 2024 (as `mcp.server.fastmcp`)
- **FastMCP 2.x** — stable standalone release, extends beyond the SDK
- **FastMCP 3.0** — beta, adds providers, transforms, hot reload, background tasks

Migration from SDK-bundled to standalone is often just changing the import:
```python
# From SDK-bundled:
from mcp.server.fastmcp import FastMCP
# To standalone:
from fastmcp import FastMCP
```

## Community Resources

### Official

- [MCP Specification](https://modelcontextprotocol.io/specification/2025-06-18)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Build a Server Tutorial](https://modelcontextprotocol.io/docs/develop/build-server)
- [MCP Blog](https://blog.modelcontextprotocol.io/)
- [Anthropic MCP Course (Skilljar)](https://anthropic.skilljar.com/introduction-to-model-context-protocol)
- [create-python-server Template](https://github.com/modelcontextprotocol/create-python-server)

### FastMCP

- [FastMCP Documentation](https://gofastmcp.com/)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [FastMCP Testing Patterns](https://gofastmcp.com/patterns/testing)
- [Stop Vibe-Testing Your MCP Server](https://www.jlowin.dev/blog/stop-vibe-testing-mcp-servers)

### Tutorials and Guides

- [Real Python: MCP Server Tutorial](https://realpython.com/python-mcp/)
- [DigitalOcean: MCP Server — Everything I Wish I'd Known on Day One](https://www.digitalocean.com/community/tutorials/mcp-server-python)
- [Microsoft MCP for Beginners](https://github.com/microsoft/mcp-for-beginners)
- [15 Best Practices for Building MCP Servers in Production](https://thenewstack.io/15-best-practices-for-building-mcp-servers-in-production/)

### Security

- [Simon Willison: MCP Prompt Injection](https://simonwillison.net/2025/Apr/9/mcp-prompt-injection/)
- [The Lethal Trifecta for AI Agents](https://simonw.substack.com/p/the-lethal-trifecta-for-ai-agents)
- [MCP Security Best Practices (Spec)](https://modelcontextprotocol.io/specification/draft/basic/security_best_practices)

### Curated Lists

- [awesome-mcp-servers (punkpeye)](https://github.com/punkpeye/awesome-mcp-servers)
- [awesome-mcp-servers (wong2)](https://github.com/wong2/awesome-mcp-servers)
- [Docker MCP Toolkit](https://docs.docker.com/ai/mcp-catalog-and-toolkit/get-started/)
