# Claude Agent SDK -- Full Reference

Deep-dive reference material for the Claude Agent SDK. Load alongside the [Agentic SDKs](../SKILL.md) skill and a language context.

## Architecture

The Claude Agent SDK wraps the Claude Code CLI, giving agents the same tools, agent loop, and context management that power Claude Code. The SDK implements a four-phase feedback cycle:

1. **Gather Context** -- Search, read files, inspect codebase
2. **Take Action** -- Execute tools (edit files, run commands)
3. **Verify Work** -- Evaluate output against criteria
4. **Iterate** -- Repeat until objectives are met

### Design Philosophy

"Give agents a computer." Instead of defining individual tool schemas, agents get filesystem access, command execution, and web capabilities out of the box. Tools should be high-value actions, not low-level utilities.

## API Surface

### Two Entry Points

| Component | Purpose | Custom Tools | Hooks | State |
|-----------|---------|-------------|-------|-------|
| `query()` | One-shot async queries | Via MCP servers | Via options | Stateless (unless `resume`) |
| `ClaudeSDKClient` | Bidirectional conversations | Yes (SDK MCP) | Yes | Stateful within `async with` |

### ClaudeAgentOptions (Python) / Options (TypeScript)

Full configuration object. Key fields:

| Field | Python | TypeScript | Description |
|-------|--------|------------|-------------|
| System prompt | `system_prompt` | `systemPrompt` | Custom or preset (`claude_code`) |
| Max turns | `max_turns` | `maxTurns` | Conversation turn limit |
| Working dir | `cwd` | `cwd` | Agent working directory |
| CLI path | `cli_path` | `pathToClaudeCodeExecutable` | Custom CLI location |
| Tools | `allowed_tools` | `allowedTools` | List of allowed tool names |
| Disallowed tools | -- | `disallowedTools` | Explicit tool blocklist |
| Permission mode | `permission_mode` | `permissionMode` | `default`, `acceptEdits`, `bypassPermissions`, `plan` |
| Custom permissions | `can_use_tool` | `canUseTool` | Callback for custom authorization |
| MCP servers | `mcp_servers` | `mcpServers` | Server configurations |
| Agents | `agents` | `agents` | Subagent definitions |
| Hooks | `hooks` | `hooks` | Event-based lifecycle hooks |
| Output format | `output_format` | `outputFormat` | JSON Schema for structured output |
| Settings | `setting_sources` | `settingSources` | Which filesystem settings to load |
| Resume | `resume` | `resume` | Session ID to resume |
| Fork | `fork_session` | `forkSession` | Fork instead of continuing |
| Model | `model` | `model` | Claude model ID |
| Fallback model | -- | `fallbackModel` | Fallback if primary fails |
| Max budget | -- | `maxBudgetUsd` | Cost cap in USD |
| Max thinking | -- | `maxThinkingTokens` | Thinking budget |
| Sandbox | -- | `sandbox` | Sandbox configuration |
| Plugins | -- | `plugins` | Plugin configurations |
| Betas | -- | `betas` | Beta features (e.g., 1M context) |
| Checkpointing | -- | `enableFileCheckpointing` | Track file changes for rewind |

### Setting Sources

| Value | Location | Content |
|-------|----------|---------|
| `"user"` | `~/.claude/settings.json` | Global user settings |
| `"project"` | `.claude/settings.json` | Shared project settings + CLAUDE.md |
| `"local"` | `.claude/settings.local.json` | Gitignored local settings |

**Default: empty** (no filesystem settings loaded). Set `["project"]` to load CLAUDE.md.

## Built-in Tools

| Tool | Description |
|------|-------------|
| `Read` | Read files (text, images, PDFs, notebooks) |
| `Write` | Create or overwrite files |
| `Edit` | Precise string replacements |
| `Bash` | Execute shell commands (with timeout, background) |
| `Glob` | Find files by glob pattern |
| `Grep` | Search file contents with regex (ripgrep) |
| `WebSearch` | Web search with domain filtering |
| `WebFetch` | Fetch and parse web pages |
| `Task` | Spawn subagents |
| `AskUserQuestion` | Ask user clarifying questions |
| `NotebookEdit` | Edit Jupyter notebook cells |
| `ExitPlanMode` | Exit planning mode |
| `ListMcpResources` | List MCP resources |
| `ReadMcpResource` | Read MCP resource |
| `KillBash` | Kill background bash process |

## Custom Tools via In-Process MCP

The SDK supports in-process MCP servers that run in the same process (no subprocess overhead).

### Python

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("tool_name", "description", {"param": type})
async def my_tool(args):
    return {"content": [{"type": "text", "text": "result"}]}

server = create_sdk_mcp_server(name="my-server", version="1.0.0", tools=[my_tool])
```

### TypeScript

```typescript
import { tool, createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

const myTool = tool("tool_name", "description", { param: z.string() },
  async (args) => ({ content: [{ type: "text" as const, text: "result" }] })
);

const server = createSdkMcpServer({ name: "my-server", tools: [myTool] });
```

### MCP Server Types

| Type | Python | TypeScript | Description |
|------|--------|------------|-------------|
| SDK (in-process) | `create_sdk_mcp_server()` | `createSdkMcpServer()` | Same-process, no IPC |
| Stdio | `{"command": "...", "args": [...]}` | `{ command: "...", args: [...] }` | Subprocess via stdin/stdout |
| SSE | `{"type": "sse", "url": "..."}` | `{ type: "sse", url: "..." }` | Server-Sent Events |
| HTTP | `{"type": "http", "url": "..."}` | `{ type: "http", url: "..." }` | HTTP transport |

Tool naming: `mcp__<server_name>__<tool_name>` (must match in `allowed_tools`).

## Subagents

### AgentDefinition

| Field | Required | Description |
|-------|----------|-------------|
| `description` | Yes | When to use this agent (natural language) |
| `prompt` | Yes | Agent system prompt |
| `tools` | No | Allowed tools (inherits all if omitted) |
| `model` | No | `"sonnet"`, `"opus"`, `"haiku"`, `"inherit"` |

### Model Tiering Pattern

```python
agents={
    "orchestrator": AgentDefinition(
        description="Complex reasoning and planning",
        prompt="...",
        model="opus",
    ),
    "worker": AgentDefinition(
        description="Simple file operations",
        prompt="...",
        model="haiku",
        tools=["Read", "Write"],
    ),
}
```

### Constraints

- Subagents **cannot spawn subagents** (single level of delegation)
- Maximum concurrent subagent limits not specified
- Subagent messages include `parent_tool_use_id` for tracking

## Hooks System

### Events

| Event | Trigger | Use Cases |
|-------|---------|-----------|
| `PreToolUse` | Before tool execution | Validate, block, modify tool input |
| `PostToolUse` | After successful tool execution | Audit, log, inject context |
| `PostToolUseFailure` | After tool failure | Error recovery, logging |
| `Stop` | Agent stopping | Cleanup, final validation |
| `SubagentStart` | Subagent spawned | Track delegations |
| `SubagentStop` | Subagent finished | Aggregate results |
| `SessionStart` | Session begins | Initialize state |
| `SessionEnd` | Session ends | Cleanup, persist data |
| `UserPromptSubmit` | User sends prompt | Pre-process input |
| `PreCompact` | Before context compaction | Add custom compaction instructions |
| `Notification` | Agent sends notification | Alert, forward |
| `PermissionRequest` | Tool needs permission | Custom authorization (TS only) |

### Hook Output Structure

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask",
    "permissionDecisionReason": "Explanation",
    "updatedInput": {}
  }
}
```

### Permission Decision Priority

`deny` > `ask` > `allow` > default `ask`

### Matcher Syntax

Matchers are regex patterns against tool names:

- `"Bash"` -- Matches Bash tool only
- `"Edit|Write"` -- Matches Edit or Write
- `"mcp__.*"` -- Matches all MCP tools
- No matcher -- Matches all tools

## Permission Modes

| Mode | Behavior |
|------|----------|
| `default` | Standard prompting for dangerous operations |
| `acceptEdits` | Auto-accept file edits, prompt for others |
| `bypassPermissions` | Skip all permission checks (requires explicit flag in TS) |
| `plan` | Planning mode -- no execution |

## Session Management

### Operations

| Operation | Description |
|-----------|-------------|
| Resume | Continue conversation with `resume=session_id` |
| Fork | Branch from existing with `fork_session=True` |
| Rewind | Restore files to checkpoint with `rewindFiles(uuid)` (TS, requires `enableFileCheckpointing`) |

### Compaction

Automatic context summarization when approaching limits. `PreCompact` hook allows injecting custom instructions.

## Structured Outputs

JSON Schema validation via `output_format` / `outputFormat`:

```python
output_format={
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "findings": {"type": "array", "items": {"type": "string"}},
            "score": {"type": "number", "minimum": 0, "maximum": 100},
        },
        "required": ["findings", "score"],
    },
}
```

Available in `ResultMessage.structured_output` (Python) or `msg.structured_output` (TS).

## Message Types

| Message | Type Field | Description |
|---------|-----------|-------------|
| `AssistantMessage` | `"assistant"` | Claude's response (text + tool use blocks) |
| `UserMessage` | `"user"` | User input |
| `SystemMessage` | `"system"` | System events (init, compact boundary) |
| `ResultMessage` | `"result"` | Final result with cost, usage, duration |
| `PartialAssistantMessage` | `"stream_event"` | Streaming events (requires `includePartialMessages`) |

### ResultMessage Fields

| Field | Description |
|-------|-------------|
| `result` | Final text output |
| `structured_output` | Parsed JSON (if `output_format` set) |
| `total_cost_usd` | Total cost in USD |
| `duration_ms` | Total duration |
| `num_turns` | Number of turns used |
| `usage` | Token usage statistics |
| `modelUsage` | Per-model usage breakdown |
| `permission_denials` | List of denied tool uses |

## Sandbox Configuration (TypeScript)

```typescript
sandbox: {
  enabled: true,
  autoAllowBashIfSandboxed: true,
  excludedCommands: ["docker"],
  allowUnsandboxedCommands: false,
  network: {
    allowLocalBinding: true,
    allowUnixSockets: ["/var/run/docker.sock"],
  },
  ignoreViolations: {
    file: ["/tmp/*"],
    network: ["localhost:*"],
  },
}
```

**Filesystem and network restrictions** use permission rules, not sandbox settings.

## Error Types

### Python

| Error | Description |
|-------|-------------|
| `ClaudeSDKError` | Base error |
| `CLINotFoundError` | Claude Code CLI not found |
| `CLIConnectionError` | Connection to CLI failed |
| `ProcessError` | CLI process failed (has `exit_code`) |
| `CLIJSONDecodeError` | Failed to parse CLI response |

### TypeScript

Same error classes plus `AbortError` for cancelled operations.

## Observability

### Built-in OpenTelemetry Spans

5 span types: agent execution, tool calls, model invocations, subagent lifecycle, session events.

### Third-Party Integrations

Langfuse, LangSmith, Datadog, and others via OpenTelemetry export.

### ResultMessage Metrics

Every completed query returns: `total_cost_usd`, `duration_ms`, `duration_api_ms`, `num_turns`, `usage` (token counts), `modelUsage` (per-model breakdown).

## Deployment Patterns

### Secure Deployment

- **Proxy pattern:** Isolate API credentials from agent process
- **Sandbox:** gVisor, container, or VM isolation
- **Permission hooks:** Custom `canUseTool` for authorization
- **Network sandboxing:** Restrict outbound connections

### Claude Code Features via SDK

Load filesystem-based configuration with `settingSources: ["project"]`:

| Feature | Location |
|---------|----------|
| Skills | `.claude/skills/SKILL.md` |
| Slash commands | `.claude/commands/*.md` |
| Memory (CLAUDE.md) | `CLAUDE.md` or `.claude/CLAUDE.md` |
| Plugins | Programmatic via `plugins` option |

## Migration from Claude Code SDK (v0.0.x)

Breaking changes in v0.1.0+:

- `ClaudeCodeOptions` renamed to `ClaudeAgentOptions` (Python)
- System prompt merged into main options
- Settings isolation: no filesystem settings loaded by default
- New subagents and session forking features
