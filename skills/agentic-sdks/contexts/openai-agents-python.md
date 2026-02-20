# OpenAI Agents SDK -- Python

Python-specific implementation guide. Load alongside the generic [Agentic SDKs](../SKILL.md) skill.

**Related skills:**
- [Python Development](../../python-development/SKILL.md) -- type hints, testing, code quality, async patterns
- [Python Project Management](../../python-prj-mgmt/SKILL.md) -- uv/pixi setup, dependency management

## Setup

```bash
pip install openai-agents
# Optional extras:
pip install 'openai-agents[voice]'   # Voice/realtime
pip install 'openai-agents[redis]'   # Redis sessions
```

Requires Python 3.10+ and `OPENAI_API_KEY` environment variable.

## Core Abstractions

### Agent

```python
from agents import Agent

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",  # Static or dynamic
    tools=[my_tool],
    handoffs=[other_agent],
    output_type=MyPydanticModel,  # Structured output
    model="gpt-4o",
    model_settings=ModelSettings(temperature=0.7),
    input_guardrails=[my_guardrail],
    output_guardrails=[my_output_guardrail],
    hooks=MyAgentHooks(),
)
```

**Dynamic instructions** -- function receiving context and agent:

```python
def dynamic_instructions(ctx: RunContextWrapper[UserInfo], agent: Agent) -> str:
    return f"Help user {ctx.context.name} with their request."

agent = Agent(name="Helper", instructions=dynamic_instructions)
```

### Runner

```python
from agents import Runner

# Async (preferred)
result = await Runner.run(agent, "Your prompt", context=my_context)

# Synchronous wrapper
result = Runner.run_sync(agent, "Your prompt")

# Streaming
result = Runner.run_streamed(agent, "Your prompt")
async for event in result.stream_events():
    print(event)

# Result access
print(result.final_output)        # Final text or structured output
print(result.to_input_list())     # For multi-turn continuation
```

**RunConfig** for global overrides:

```python
from agents import RunConfig

config = RunConfig(
    model="gpt-4o",
    max_turns=10,
    tracing_disabled=False,
)
result = await Runner.run(agent, "prompt", run_config=config)
```

## Tools

### Function Tools

```python
from agents import function_tool

@function_tool
def get_weather(city: str) -> str:
    """Get the weather for a given city."""
    return f"Weather in {city}: sunny, 22C"

@function_tool
async def search_database(
    query: str,
    limit: int = 10
) -> list[dict]:
    """Search the database for records matching query."""
    return await db.search(query, limit=limit)
```

**With context access:**

```python
@function_tool
async def get_user_data(ctx: RunContextWrapper[UserInfo]) -> str:
    return f"User: {ctx.context.name}, ID: {ctx.context.uid}"
```

**With Pydantic constraints:**

```python
from pydantic import Field

@function_tool
def score(value: int = Field(..., ge=0, le=100)) -> str:
    return f"Score: {value}"
```

**Custom function tools:**

```python
from agents import FunctionTool

custom_tool = FunctionTool(
    name="custom_search",
    description="Search with custom logic",
    params_json_schema={"type": "object", "properties": {"q": {"type": "string"}}},
    on_invoke_tool=my_async_handler,
)
```

### Agents as Tools

```python
translator = Agent(name="Translator", instructions="Translate text.")
main_agent = Agent(
    name="Main",
    tools=[translator.as_tool(
        tool_name="translate",
        tool_description="Translate text between languages",
    )],
)
```

### Hosted Tools

```python
from agents import Agent, WebSearchTool, FileSearchTool, CodeInterpreterTool

agent = Agent(
    name="Research",
    tools=[
        WebSearchTool(),
        FileSearchTool(vector_store_ids=["vs_123"]),
        CodeInterpreterTool(),
    ],
)
```

## Handoffs

```python
from agents import Agent, handoff

billing = Agent(name="Billing", instructions="Handle billing questions.")
support = Agent(name="Support", instructions="Handle support questions.")

triage = Agent(
    name="Triage",
    instructions="Route customer requests to the right team.",
    handoffs=[billing, handoff(support, on_handoff=log_escalation)],
)
```

**With structured input:**

```python
from pydantic import BaseModel

class EscalationData(BaseModel):
    reason: str
    priority: int

async def on_escalate(ctx: RunContextWrapper, data: EscalationData):
    print(f"Escalation: {data.reason} (priority {data.priority})")

handoff_obj = handoff(
    agent=escalation_agent,
    on_handoff=on_escalate,
    input_type=EscalationData,
)
```

## Guardrails

### Input Guardrails

```python
from agents import input_guardrail, GuardrailFunctionOutput, InputGuardrailTripwireTriggered

@input_guardrail
async def safety_check(ctx, agent, input: str) -> GuardrailFunctionOutput:
    result = await Runner.run(checker_agent, input, context=ctx.context)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_unsafe,
    )

agent = Agent(name="Safe Agent", input_guardrails=[safety_check])

try:
    await Runner.run(agent, user_input)
except InputGuardrailTripwireTriggered:
    print("Input rejected by guardrail")
```

### Output Guardrails

```python
from agents import output_guardrail, OutputGuardrailTripwireTriggered

@output_guardrail
async def quality_check(ctx, agent, output) -> GuardrailFunctionOutput:
    return GuardrailFunctionOutput(
        output_info="checked",
        tripwire_triggered=len(output.response) < 10,
    )
```

### Tool Guardrails

```python
from agents import tool_input_guardrail, tool_output_guardrail, ToolGuardrailFunctionOutput

@tool_input_guardrail
def block_secrets(data):
    if "sk-" in json.dumps(data.context.tool_arguments or {}):
        return ToolGuardrailFunctionOutput.reject_content("Remove secrets first.")
    return ToolGuardrailFunctionOutput.allow()

@function_tool(tool_input_guardrails=[block_secrets])
def classify(text: str) -> str:
    return f"classified: {text}"
```

## Context Management

```python
from dataclasses import dataclass

@dataclass
class AppContext:
    user_id: str
    db: Database
    permissions: list[str]

agent = Agent[AppContext](name="App", tools=[my_tool])
result = await Runner.run(
    agent, "Do something",
    context=AppContext(user_id="u1", db=db, permissions=["read"]),
)
```

**The context object is NOT sent to the LLM.** Access data in tools via `ctx.context`.

## Sessions

```python
from agents.extensions.sessions import SQLiteSession

session = SQLiteSession("conversations.db")

result = await Runner.run(
    agent, "Hello",
    session=session,
    session_id="user-123",
)
# History persisted automatically. No manual to_input_list() needed.
```

## Tracing

```python
from agents import trace

with trace("My workflow"):
    result1 = await Runner.run(agent, "Step 1")
    result2 = await Runner.run(agent, f"Step 2: {result1.final_output}")
```

Disable: `OPENAI_AGENTS_DISABLE_TRACING=1` or `RunConfig(tracing_disabled=True)`.

## MCP Integration

```python
from agents.mcp import MCPServerStdio, MCPServerStreamableHttp

# Stdio server
stdio_server = MCPServerStdio(
    params={"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]},
    cache_tools_list=True,
)

# HTTP server
http_server = MCPServerStreamableHttp(url="http://localhost:8080/mcp")

agent = Agent(name="MCP Agent", mcp_servers=[stdio_server, http_server])

async with stdio_server, http_server:
    result = await Runner.run(agent, "List files in /tmp")
```

## Error Handling

Key exceptions: `MaxTurnsExceeded`, `ModelBehaviorError`, `ToolTimeoutError`, `InputGuardrailTripwireTriggered`, `OutputGuardrailTripwireTriggered`.

## Common Pitfalls

- Forgetting `async with` for MCP servers (they need lifecycle management)
- Using `Runner.run_sync()` inside async code (use `Runner.run()` instead)
- Not handling `MaxTurnsExceeded` -- set reasonable `max_turns` and catch the exception
- Context type mismatch -- all agents, tools, and hooks in a run must share the same context type
- Forgetting that `RunContextWrapper.context` is not sent to the LLM
