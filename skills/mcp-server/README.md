# MCP Server Skill

Guidance for building [Model Context Protocol](https://modelcontextprotocol.io) servers in Python using the official SDK (`mcp` package) and FastMCP framework.

## When to Use

- Creating a new MCP server from scratch
- Defining tools, resources, or prompts for an MCP server
- Configuring transports (stdio, streamable HTTP)
- Testing MCP servers with pytest or the MCP Inspector
- Integrating with Claude Desktop or Claude Code
- Packaging MCP servers as bundles (`.mcpb`) for distribution
- Deploying MCP servers (Docker, PyPI, Starlette mounting)
- Debugging MCP server issues (logging, error handling, stdout corruption)

## Activation

The skill activates automatically when the agent detects tasks related to:

- Creating or modifying MCP servers
- Working with `mcp.server.fastmcp`, `FastMCP`, or `MCPServer`
- Defining `@mcp.tool()`, `@mcp.resource()`, or `@mcp.prompt()` decorators
- Configuring MCP transports or client integration
- Running `mcp dev`, `mcp run`, or `mcp install`
- Packaging with `mcpb init`, `mcpb pack`, or creating `manifest.json`

Trigger explicitly by asking about "MCP server," "MCP bundle," "building an MCP tool," or referencing this skill by name.

## Skill Contents

| File | Purpose |
|------|---------|
| `SKILL.md` | Core reference: SDK landscape, quickstart, primitives (tools, resources, prompts), transports, lifespan, logging, testing, client integration, bundles (.mcpb), error handling, project structure, CLI, common pitfalls |
| `README.md` | This file — overview and usage guide |
| `references/resources.md` | Deep-dive: bundle manifest spec, server composition, security, deployment, SDK migration, community resources |

## Quick Start

1. **Load the skill**: reference `mcp-server` when starting MCP development work
2. **Scaffold**: `uv init --package mcp-server-myproject && uv add "mcp[cli]"`
3. **Define primitives**: Use `@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()` decorators
4. **Test**: `uv run mcp dev src/server.py` (Inspector) + pytest with in-memory client
5. **Integrate**: `claude mcp add` (Claude Code) or `uv run mcp install` (Claude Desktop)
6. **Package** (optional): `mcpb init && mcpb pack` to create a `.mcpb` bundle

## Related Skills

- **[python](../python/)** — Type hints, testing, code quality, async patterns
- **[python-prj-mgmt](../python-prj-mgmt/)** — uv/pixi setup, dependency management, pyproject.toml configuration

## Testing

**Test MCP server creation guidance:**

```
# Ask about creating an MCP server — the skill should activate automatically
> I want to build an MCP server that exposes a database query tool

# Or reference it explicitly
> Using the mcp-server skill, help me add a resource to my MCP server
```

**Test debugging guidance:**

```
> My MCP server tools aren't showing up in Claude Desktop
> How do I test my MCP server with pytest?
```
