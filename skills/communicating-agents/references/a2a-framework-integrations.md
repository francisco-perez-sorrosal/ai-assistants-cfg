# A2A Framework Integrations

Integration patterns for exposing framework-built agents via A2A. Load alongside the [Communicating Agents](../SKILL.md) skill.

## Integration Landscape

| Framework | Integration Type | Effort | Notes |
|-----------|-----------------|--------|-------|
| Google ADK | Native | Minimal | Built-in A2A server and client |
| Pydantic AI | One-liner | Minimal | `agent.to_a2a()` |
| LangGraph | Platform feature | Low | A2A endpoint via LangSmith/Agent Server |
| CrewAI | Adapter | Low | A2A adapter wraps crews |
| Semantic Kernel | Plugin | Medium | A2A plugin for .NET agents |
| AutoGen / MS Agent Framework | Connector | Medium | A2A connector |
| LlamaIndex | Integration | Medium | A2A agent integration |
| AWS Bedrock AgentCore | Native deployment | Low | Deploy as A2A-compatible service |
| Google Cloud Run / Vertex AI | Native deployment | Low | Deploy as A2A-compatible service |

## Google ADK (Agent Development Kit)

Native A2A support -- ADK agents can act as both A2A servers and clients.

### Exposing an ADK Agent via A2A

```python
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.a2a import A2AServer

agent = Agent(
    name="my-adk-agent",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant.",
)

# Wrap ADK agent as A2A server
runner = Runner(agent=agent, app_name="my-app", session_service=...)
server = A2AServer(runner=runner)
server.start(port=8000)
```

### Calling an A2A Agent from ADK

```python
from google.adk.tools.a2a_tool import A2ATool

# Register remote A2A agent as a tool
remote_tool = A2ATool(
    agent_card_url="https://remote-agent.example.com/.well-known/agent-card.json"
)

orchestrator = Agent(
    name="orchestrator",
    model="gemini-2.0-flash",
    tools=[remote_tool],
)
```

### Sample Agents

The `a2a-samples` repo includes several ADK examples:
- **Expense Reimbursement** -- multi-step approval workflow
- **Purchasing Concierge** -- ADK client orchestrating multiple A2A agents

## LangGraph

A2A endpoint available through LangSmith Platform / Agent Server.

### Exposing a LangGraph Agent

```python
# LangGraph agents deployed via LangSmith get A2A endpoints automatically
# Configure in the LangSmith dashboard or via deployment config

# The platform handles:
# - Agent Card generation from graph metadata
# - JSON-RPC endpoint
# - Task lifecycle management
# - Streaming support
```

### Sample

- **Currency Agent** -- LangGraph-based agent in `a2a-samples`
- **Pizza Agent** -- order processing with LangGraph

## CrewAI

A2A adapter wraps CrewAI crews as A2A-compatible agents.

### Exposing a Crew via A2A

```python
from crewai import Agent, Crew, Task
# CrewAI provides an A2A adapter that wraps the crew
# See a2a-samples/crewai for the full pattern

crew = Crew(
    agents=[...],
    tasks=[...],
)

# Wrap with A2A adapter (exact API depends on CrewAI version)
# The adapter handles:
# - Agent Card from crew metadata
# - Task mapping (A2A Task <-> CrewAI Task)
# - Message routing to appropriate crew agents
```

### Sample

- **Burger Agent** -- CrewAI crew wrapped as A2A agent in `a2a-samples`

## Pydantic AI

Direct A2A conversion with `to_a2a()`.

```python
from pydantic_ai import Agent

agent = Agent(
    "openai:gpt-4o",
    system_prompt="You are a helpful assistant.",
)

# One-liner: expose as A2A server
a2a_app = agent.to_a2a()

# Run with uvicorn
import uvicorn
uvicorn.run(a2a_app, host="0.0.0.0", port=8000)
```

The `to_a2a()` method automatically:
- Generates an Agent Card from agent metadata
- Maps Pydantic AI tools to A2A skills
- Handles task lifecycle and streaming

## Semantic Kernel

A2A plugin for .NET-based agents.

```csharp
// Register A2A agent as a Semantic Kernel plugin
var a2aPlugin = new A2APlugin(
    agentCardUrl: "https://remote-agent.example.com/.well-known/agent-card.json"
);

kernel.Plugins.Add(a2aPlugin);
// Agent skills appear as kernel functions
```

## AutoGen / Microsoft Agent Framework

A2A connector enables AutoGen agents to participate in A2A networks.

```python
# AutoGen agents can be wrapped as A2A servers
# and can call remote A2A agents as tools
# See a2a-samples/autogen for examples
```

## LlamaIndex

A2A integration for LlamaIndex agents.

```python
# LlamaIndex provides A2A integration
# allowing agents to discover and call A2A services
# See a2a-samples/llamaindex for examples
```

## AWS Bedrock AgentCore

Deploy agents as A2A-compatible services on AWS infrastructure.

- Native deployment target for A2A agents
- Handles scaling, security, and networking
- Integrates with AWS IAM for authentication

## Community Alternatives

### FastA2A (Pydantic team)

Lightweight A2A server framework built on FastAPI.

```python
from fast_a2a import FastA2A

app = FastA2A(
    name="my-agent",
    description="A fast A2A agent",
)

@app.skill("process")
async def process(message: str) -> str:
    return f"Processed: {message}"
```

### python-a2a

Community A2A implementation with a simplified API.

```python
from python_a2a import A2AServer

server = A2AServer(name="my-agent")

@server.handler
async def handle(message):
    return f"Response to: {message.text}"
```

## Integration Patterns

### Framework Agent as A2A Server

The most common pattern: wrap an existing framework agent to accept A2A requests.

```
External A2A Client --> A2A Adapter --> Framework Agent --> LLM/Tools
```

**Adapter responsibilities:**
1. Parse A2A `SendMessage` into framework-native input
2. Map framework output to A2A `Message`/`Artifact`
3. Manage task lifecycle (state transitions, history)
4. Serve Agent Card for discovery

### A2A Agent as Framework Tool

Register remote A2A agents as tools within your framework:

```
Framework Orchestrator --> A2A Client --> Remote A2A Agent
```

**Pattern:** Create a tool/function that wraps `A2AClient.send_message()`, letting the orchestrator delegate to remote agents transparently.

### Multi-Framework Orchestration

Combine agents from different frameworks via A2A:

```
ADK Orchestrator (A2A Client)
  |-> LangGraph Agent (A2A Server)
  |-> CrewAI Crew (A2A Server)
  |-> Custom Agent (A2A Server)
```

Each agent exposes its Agent Card. The orchestrator discovers capabilities and routes tasks based on skill matching.

## Resources

- [A2A Samples](https://github.com/a2aproject/a2a-samples) -- reference implementations for all major frameworks
- [Google ADK docs](https://google.github.io/adk-docs/)
- [FastA2A](https://github.com/pydantic/FastA2A)
