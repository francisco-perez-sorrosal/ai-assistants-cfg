# MCP Crafting Skill

Guidance for building [Model Context Protocol](https://modelcontextprotocol.io) servers. Language-specific implementation modules available, starting with Python.

## When to Use

- Creating a new MCP server
- Defining tools, resources, or prompts for an MCP server
- Configuring transports (stdio, streamable HTTP)
- Testing MCP servers with the MCP Inspector or language-specific test frameworks
- Integrating with Claude Desktop, Claude Code, or Cursor
- Packaging MCP servers as bundles (`.mcpb`) for distribution
- Deploying MCP servers (Docker, containers, package registries)
- Debugging MCP server issues (logging, error handling, stdout corruption)

## Activation

The skill activates automatically when the agent detects tasks related to:

**Protocol-level triggers:**

- Creating or modifying MCP servers
- Configuring MCP transports or client integration
- Defining MCP tools, resources, or prompts
- Packaging with `mcpb init`, `mcpb pack`, or creating `manifest.json`
- Running `mcp dev`, `mcp run`, or `mcp install`

**Python context triggers** (additionally loads `contexts/python.md`):

- Working with `mcp.server.fastmcp`, `FastMCP`, or `MCPServer`
- Using `@mcp.tool()`, `@mcp.resource()`, or `@mcp.prompt()` decorators
- Working in a Python project with MCP dependencies (`mcp[cli]`, `fastmcp`)

Trigger explicitly by asking about "MCP server," "MCP bundle," "building an MCP tool," or referencing this skill by name.

## Skill Contents

| File | Purpose |
|------|---------|
| [`SKILL.md`](SKILL.md) | Protocol core: MCP concepts, transports, client integration, error handling, bundles overview, MCP Inspector, common pitfalls |
| [`README.md`](README.md) | This file -- overview and usage guide |
| [`contexts/python.md`](contexts/python.md) | Python implementation: SDK landscape, quickstart, primitives code, testing, project structure, deployment |
| [`references/resources.md`](references/resources.md) | Protocol deep-dive: bundle manifest spec, security, team sharing, community resources |
| [`references/python-resources.md`](references/python-resources.md) | Python deep-dive: server composition, deployment, SDK versions, Python community resources |

## Quick Start

1. **Load the skill**: reference `mcp-crafting` when starting MCP development work
2. **Choose language context**: load the context for your language (Python: [`contexts/python.md`](contexts/python.md))
3. **Scaffold**: create a project with your language's package manager (Python: `uv init --package mcp-server-myproject && uv add "mcp[cli]"`)
4. **Define primitives**: implement tools, resources, and prompts using your SDK's decorator or handler API
5. **Test**: use the MCP Inspector (`npx -y @modelcontextprotocol/inspector`) and language-specific test frameworks
6. **Integrate**: `claude mcp add` (Claude Code) or register with Claude Desktop
7. **Package** (optional): `mcpb init && mcpb pack` to create a `.mcpb` bundle

## Testing

**Test protocol-level guidance:**

```
# Ask about MCP concepts -- the skill should activate automatically
> What are MCP tools vs resources?

# Ask about bundles or distribution
> How do I package my MCP server as a bundle?
```

**Test language-specific guidance:**

```
# Ask about creating an MCP server in a specific language
> I want to build an MCP server in Python that exposes a database query tool

# Or reference it explicitly
> Using the mcp-crafting skill, help me add a resource to my Python MCP server
```

**Test debugging guidance:**

```
> My MCP server tools aren't showing up in Claude Desktop
> How do I test my MCP server?
```

## Related Skills

Python context:

- [`python-development`](../python-development/) -- type hints, testing, code quality, async patterns
- [`python-prj-mgmt`](../python-prj-mgmt/) -- uv/pixi setup, dependency management, pyproject.toml configuration
