# OpenAI Agents SDK -- Full Reference

Deep-dive reference material for the OpenAI Agents SDK. Load alongside the [Agentic SDKs](../SKILL.md) skill and a language context.

## Agent Configuration

### All Agent Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Required identifier |
| `instructions` | `str \| Callable` | System prompt (static string or dynamic function) |
| `model` | `str` | LLM model to use |
| `model_settings` | `ModelSettings` | Temperature, top_p, etc. |
| `tools` | `list[Tool]` | Available tools |
| `mcp_servers` | `list[MCPServer]` | MCP server connections |
| `handoffs` | `list[Agent \| Handoff]` | Agents for delegation |
| `output_type` | `type` | Pydantic model, dataclass, TypedDict, or list for structured output |
| `input_guardrails` | `list[InputGuardrail]` | Pre-execution validation |
| `output_guardrails` | `list[OutputGuardrail]` | Post-execution validation |
| `hooks` | `AgentHooks` | Lifecycle event observers |
| `tool_use_behavior` | `str \| StopAtTools \| ToolsToFinalOutputFunction` | How tool outputs are processed |
| `reset_tool_choice` | `bool` | Prevent tool-use loops (default: True) |
| `prompt` | `str` | References prompt templates by ID (Responses API) |

### ModelSettings.tool_choice

- `"auto"` -- LLM decides tool usage
- `"required"` -- Forces tool use
- `"none"` -- Prohibits tool use
- `"<tool_name>"` -- Forces specific tool

### tool_use_behavior Modes

- `"run_llm_again"` -- Default. LLM processes tool results for final response
- `"stop_on_first_tool"` -- First tool output becomes final response
- `StopAtTools(stop_at_tool_names=[...])` -- Halt on specified tools
- `ToolsToFinalOutputFunction` -- Custom function deciding continuation

### Agent Cloning

```python
new_agent = agent.clone(name="Modified Agent", instructions="New instructions")
```

## Runner Details

### Execution Methods

| Method | Async | Returns | Use Case |
|--------|-------|---------|----------|
| `Runner.run()` | Yes | `RunResult` | Production async code |
| `Runner.run_sync()` | No | `RunResult` | Scripts, testing |
| `Runner.run_streamed()` | Yes | `RunResultStreaming` | Real-time UI updates |

### RunResult

```python
result.final_output       # str or structured type
result.to_input_list()    # For multi-turn continuation
result.last_agent         # Agent that produced the output
result.new_items          # Items generated during the run
```

### RunConfig

| Parameter | Description |
|-----------|-------------|
| `model` | Override all agent models |
| `model_settings` | Global temperature, top_p, etc. |
| `max_turns` | Maximum agent loop iterations |
| `input_guardrails` | Global input guardrails |
| `output_guardrails` | Global output guardrails |
| `handoff_input_filter` | Edit handoff inputs |
| `nest_handoff_history` | Collapse transcript (beta) |
| `tracing_disabled` | Disable observability |
| `call_model_input_filter` | Modify input pre-call |
| `tool_error_formatter` | Custom error messages |

### Multi-Turn Conversations

**Manual:**

```python
new_input = result.to_input_list() + [{"role": "user", "content": "Follow-up"}]
result = await Runner.run(agent, new_input)
```

**Sessions (automatic):**

```python
from agents.extensions.sessions import SQLiteSession
session = SQLiteSession("conversations.db")
result = await Runner.run(agent, "Hello", session=session, session_id="user-123")
```

**Server-managed:**

```python
result = await Runner.run(agent, "Hello", conversation_id="conv-123")
```

## Tool Types

### Function Tools

Decorated Python/TypeScript functions with automatic schema generation from type hints/annotations and docstring parsing (Google, Sphinx, NumPy formats).

**Output types:** `str`, `ToolOutputText`, `ToolOutputImage`, `ToolOutputFileContent`, or lists.

**Timeout (async only):**

```python
@function_tool(timeout=2.0, timeout_behavior="error_as_result")
async def slow_lookup(query: str) -> str: ...
```

**Conditional enabling:**

```python
@function_tool
def admin_tool(ctx: RunContextWrapper[AppCtx]) -> str: ...

# Enable only for admins
admin_tool.is_enabled = lambda ctx, agent: ctx.context.is_admin
```

### Hosted Tools

Available with `OpenAIResponsesModel`:

| Tool | Class | Purpose |
|------|-------|---------|
| Web Search | `WebSearchTool` | Search the web with filters |
| File Search | `FileSearchTool` | Query OpenAI Vector Stores |
| Code Interpreter | `CodeInterpreterTool` | Execute code in sandbox |
| Image Generation | `ImageGenerationTool` | Generate images from prompts |
| Hosted MCP | `HostedMCPTool` | Remote MCP server execution |
| Shell | `ShellTool` | Container execution with skills |

### Local Runtime Tools

| Tool | Class | Purpose |
|------|-------|---------|
| Computer | `ComputerTool` | GUI/browser automation |
| Shell | `ShellTool` | Local command execution |
| Apply Patch | `ApplyPatchTool` | Apply diffs locally |

### Agents as Tools

```python
specialist = Agent(name="Specialist", instructions="...")
main = Agent(
    name="Main",
    tools=[specialist.as_tool(
        tool_name="consult_specialist",
        tool_description="Consult specialist for domain questions",
        parameters=InputModel,
        max_turns=5,
        needs_approval=True,
        custom_output_extractor=my_extractor,
    )],
)
```

## Handoff Details

### Customization Parameters

| Parameter | Description |
|-----------|-------------|
| `agent` | Target agent |
| `tool_name_override` | Custom tool name (default: `transfer_to_<name>`) |
| `tool_description_override` | Custom description |
| `on_handoff` | Callback on handoff invocation |
| `input_type` | Pydantic model for structured input |
| `input_filter` | Transform conversation history before handoff |
| `is_enabled` | Boolean or callable for runtime availability |
| `nest_handoff_history` | Collapse prior transcript (beta) |

### Input Filters

Pre-built filters via `agents.extensions.handoff_filters`:

```python
from agents.extensions.handoff_filters import remove_all_tools
handoff_obj = handoff(agent=specialist, input_filter=remove_all_tools)
```

### Recommended Prompts

```python
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
agent = Agent(instructions=f"{RECOMMENDED_PROMPT_PREFIX}\nYour instructions here")
```

## Guardrail Details

### Execution Model

| Type | Runs On | Parallel | Position |
|------|---------|----------|----------|
| Input | Initial user input | Yes (default) or blocking | First agent only |
| Output | Final agent output | No (always after) | Last agent only |
| Tool Input | Before tool execution | Per-tool | Any tool |
| Tool Output | After tool execution | Per-tool | Any tool |

### Tool Guardrail Actions

```python
ToolGuardrailFunctionOutput.allow()                    # Proceed normally
ToolGuardrailFunctionOutput.reject_content("reason")   # Block with message
ToolGuardrailFunctionOutput.skip_tool_call()            # Skip without error
```

## MCP Server Types

| Type | Class | Transport | Use Case |
|------|-------|-----------|----------|
| Hosted | `HostedMCPTool` | API infrastructure | Remote servers, no local process |
| Streamable HTTP | `MCPServerStreamableHttp` | HTTP/2 | Self-managed servers |
| SSE (deprecated) | `MCPServerSse` | Server-Sent Events | Legacy servers |
| Stdio | `MCPServerStdio` | stdin/stdout | Local processes, prototypes |
| Manager | `MCPServerManager` | Mixed | Multiple servers, fault tolerance |

### Server Parameters

| Parameter | Description |
|-----------|-------------|
| `cache_tools_list` | Cache tool definitions to reduce latency |
| `require_approval` | Human-in-the-loop ("always", "never", or per-tool map) |
| `tool_meta_resolver` | Inject per-call metadata (tenant IDs, etc.) |
| `tool_filter` | Restrict exposed tools (static or dynamic) |

### Tool Filtering

```python
from agents.mcp import create_static_tool_filter

# Static
tool_filter = create_static_tool_filter(allowed_tool_names=["read_file", "write_file"])

# Dynamic
def dynamic_filter(ctx: ToolFilterContext, tools: list) -> list:
    if ctx.agent.name == "ReadOnly":
        return [t for t in tools if t.name.startswith("read")]
    return tools
```

## Tracing Architecture

### Span Types

| Span | Function | Tracks |
|------|----------|--------|
| `agent_span()` | Agent execution | Agent lifecycle |
| `generation_span()` | LLM call | Model invocation |
| `function_span()` | Tool execution | Function tool calls |
| `guardrail_span()` | Guardrail check | Safety validation |
| `handoff_span()` | Agent handoff | Delegation |
| `transcription_span()` | Speech-to-text | Voice input |
| `speech_span()` | Text-to-speech | Voice output |
| `custom_span()` | Custom operations | Application logic |

### Sensitive Data Control

```python
RunConfig(trace_include_sensitive_data=False)  # Omit LLM I/O from traces
```

Or: `OPENAI_AGENTS_TRACE_INCLUDE_SENSITIVE_DATA=false`

### External Processors

20+ integrations: Weights & Biases, Arize-Phoenix, MLflow, Braintrust, Pydantic Logfire, AgentOps, LangSmith, Langfuse, PostHog, and others.

```python
from agents.tracing import add_trace_processor
add_trace_processor(my_custom_processor)  # Keeps OpenAI backend

from agents.tracing import set_trace_processors
set_trace_processors([my_processor])      # Replaces default
```

## Error Handling

| Exception | Cause |
|-----------|-------|
| `MaxTurnsExceeded` | Agent exceeded `max_turns` |
| `ModelBehaviorError` | Invalid LLM output / malformed JSON |
| `ToolTimeoutError` | Tool execution timeout |
| `InputGuardrailTripwireTriggered` | Input guardrail triggered |
| `OutputGuardrailTripwireTriggered` | Output guardrail triggered |

### Error Handlers

```python
def on_max_turns(data) -> RunErrorHandlerResult:
    return RunErrorHandlerResult(
        final_output="Couldn't finish in time.",
        include_in_history=False,
    )

result = await Runner.run(
    agent, "prompt",
    error_handlers={"max_turns": on_max_turns},
)
```

## Long-Running Workflow Integrations

- **Temporal** -- Durable Python workflows with human approval
- **Restate** -- Lightweight orchestration with single-binary runtime
- **DBOS** -- Database-backed reliability (SQLite/Postgres)

## Experimental: Codex Tool

```python
from agents.extensions.experimental.codex import codex_tool, ThreadOptions

tool = codex_tool(
    sandbox_mode="workspace-write",
    working_directory="/path/to/repo",
    default_thread_options=ThreadOptions(model="gpt-5.2-codex"),
)
```
