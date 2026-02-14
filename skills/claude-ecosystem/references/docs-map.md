# Documentation Navigation Map

Where to find what across the Anthropic/Claude documentation ecosystem. Reference material for the [Claude Ecosystem](../SKILL.md) skill.

## platform.claude.com/docs -- Primary Developer Docs

Base URL: `https://platform.claude.com/docs/en/`

The main developer documentation (formerly `docs.anthropic.com`, which now redirects). Evergreen -- no version selector. Feature availability shown via platform badges (Claude API, Bedrock, Vertex AI, Azure AI) and beta annotations.

| Section | Path | Covers |
|---------|------|--------|
| Build with Claude | `/build-with-claude/` | Extended thinking, structured outputs, citations, batch processing, PDF support, prompt caching, token counting, compaction, Files API, data residency, 1M context |
| Agents and Tools | `/agents-and-tools/` | Tool use, web search, web fetch, code execution, memory, computer use, MCP connector, tool search, Agent Skills, fine-grained streaming |
| API Reference | `/api/` | REST endpoints (Messages, Batches, Token Counting, Files, Admin), client SDKs, errors, versioning |
| Claude Code | `/claude-code/` | IDE integration, hooks, plugins, skills, commands, Agent SDK, subagents, best practices |
| MCP | `/mcp/` | Model Context Protocol overview (links to `modelcontextprotocol.io` for spec details) |
| Release Notes | `/release-notes/` | Changelogs for API, Claude Code, and models |

**Key entry points:**

- Features overview: `/build-with-claude/overview`
- Messages API reference: `/api/messages`
- Client SDKs listing: `/api/client-sdks`
- Skill authoring best practices: `/agents-and-tools/agent-skills/best-practices`

## code.claude.com/docs -- Claude Code Docs

Base URL: `https://code.claude.com/docs/en/`

Claude Code-specific documentation. Covers operational usage, configuration, and extensibility.

| Topic | What to find |
|-------|-------------|
| Memory and settings | Configuration files, memory management, project vs global settings |
| Hooks | Pre/post command hooks, payload format, `settings.json` integration |
| Plugins | Plugin manifest, installation, cache behavior |
| Skills and commands | Authoring, activation, progressive disclosure |
| Best practices | Context management, effective prompting, workflow patterns |

**LLM-friendly index:** `https://code.claude.com/docs/llms.txt` -- structured index designed for LLM consumption. Use when an agent needs to discover Claude Code docs programmatically.

## modelcontextprotocol.io -- MCP Specification

Base URL: `https://modelcontextprotocol.io/`

The authoritative source for the Model Context Protocol. Current spec version: `2025-11-25`.

| Section | Path | Covers |
|---------|------|--------|
| Specification | `/specification/2025-11-25` | Full protocol spec (architecture, transports, lifecycle, capabilities) |
| Changelog | `/specification/2025-11-25/changelog` | Spec version history (Tasks, Elicitation, OAuth 2.1, Extensions) |
| Quickstart | `/quickstart` | Getting started guides for server and client development |
| SDKs | `/sdk` | Official Python and TypeScript SDK documentation |
| Server registry | `registry.modelcontextprotocol.io` | Official MCP server registry (replaces the deprecated README-based listing) |

## GitHub Repositories

### anthropics Organization

`https://github.com/anthropics/`

| Repo | Purpose |
|------|---------|
| [anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python) | Python SDK -- REST API client |
| [anthropic-sdk-typescript](https://github.com/anthropics/anthropic-sdk-typescript) | TypeScript SDK -- REST API client |
| [claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python) | Agent SDK (Python) -- agent framework, powers Claude Code |
| [claude-agent-sdk-typescript](https://github.com/anthropics/claude-agent-sdk-typescript) | Agent SDK (TypeScript) |
| [courses](https://github.com/anthropics/courses) | Official Anthropic courses and tutorials |
| [anthropic-cookbook](https://github.com/anthropics/anthropic-cookbook) | Code examples and patterns for common API use cases |
| [skills](https://github.com/anthropics/skills) | Official reference skill implementations |

### modelcontextprotocol Organization

`https://github.com/modelcontextprotocol/`

| Repo | Purpose |
|------|---------|
| [modelcontextprotocol](https://github.com/modelcontextprotocol/modelcontextprotocol) | MCP spec source and discussions |
| [python-sdk](https://github.com/modelcontextprotocol/python-sdk) | Official MCP Python SDK |
| [typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk) | Official MCP TypeScript SDK (npm: `@modelcontextprotocol/sdk`) |
| [servers](https://github.com/modelcontextprotocol/servers) | Reference MCP server implementations (~8 servers: filesystem, GitHub, git, Slack, etc.) |

## Quick Lookup Guide

Common developer questions and where to find answers.

| I need to... | Go to |
|--------------|-------|
| Choose a model for my use case | [SKILL.md Model Selection Heuristics](../SKILL.md) |
| Use extended thinking / effort parameter | [platform.claude.com -- Build with Claude](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) |
| Set up tool use (function calling) | [platform.claude.com -- Agents and Tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview) |
| Understand Messages API parameters | [platform.claude.com -- API Reference](https://platform.claude.com/docs/en/api/messages) |
| Configure prompt caching | [platform.claude.com -- Prompt Caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) |
| Use batch processing | [platform.claude.com -- Batch Processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing) |
| Build an MCP server | [mcp-crafting skill](../../mcp-crafting/SKILL.md) + [modelcontextprotocol.io](https://modelcontextprotocol.io/) |
| Configure Claude Code hooks/plugins | [code.claude.com docs](https://code.claude.com/docs/en/) + `claude-code-guide` subagent |
| Write a Claude Code skill | [skill-crafting skill](../../skill-crafting/SKILL.md) + [Anthropic best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) |
| Find SDK installation / quickstart | [sdk-patterns.md](sdk-patterns.md) or [platform.claude.com -- Client SDKs](https://platform.claude.com/docs/en/api/client-sdks) |
| Check API changelog / new features | [platform.claude.com -- Release Notes](https://platform.claude.com/docs/en/release-notes/overview) |
| Find example code / cookbooks | [anthropic-cookbook](https://github.com/anthropics/anthropic-cookbook) |
| Look up MCP spec details | [modelcontextprotocol.io/specification](https://modelcontextprotocol.io/specification/2025-11-25) |
| Find official MCP servers | [MCP Server Registry](https://registry.modelcontextprotocol.io/) |
