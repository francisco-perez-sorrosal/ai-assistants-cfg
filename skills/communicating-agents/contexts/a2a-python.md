# A2A Protocol -- Python SDK

Python-specific implementation guide. Load alongside the generic [Communicating Agents](../SKILL.md) skill.

## Setup

```bash
pip install a2a-sdk
# or
uv add a2a-sdk
```

Requires Python 3.10+.

**Extras** (install as needed):

| Extra | Purpose |
|-------|---------|
| `a2a-sdk[http-server]` | Starlette/Uvicorn HTTP server |
| `a2a-sdk[grpc]` | gRPC transport support |
| `a2a-sdk[telemetry]` | OpenTelemetry integration |
| `a2a-sdk[encryption]` | Payload encryption |
| `a2a-sdk[postgresql]` | PostgreSQL task persistence |
| `a2a-sdk[mysql]` | MySQL task persistence |
| `a2a-sdk[sqlite]` | SQLite task persistence |
| `a2a-sdk[sql]` | All SQL backends |
| `a2a-sdk[all]` | Everything |

## Core Classes

| Class | Module | Purpose |
|-------|--------|---------|
| `AgentExecutor` | `a2a.server.agent_execution` | Abstract base -- implement `execute()` and `cancel()` |
| `DefaultRequestHandler` | `a2a.server.request_handler` | Routes JSON-RPC requests to executor |
| `InMemoryTaskStore` | `a2a.server.tasks` | Dev-only task persistence (use SQL stores for prod) |
| `A2AStarletteApplication` | `a2a.server.apps` | HTTP server (Starlette/Uvicorn) |
| `RequestContext` | `a2a.server.agent_execution` | Request metadata (task ID, context ID, message) |
| `EventQueue` | `a2a.server.events` | Async event publishing for streaming |
| `QueueManager` | `a2a.server.events` | Manages event queues per task |
| `PushNotifier` | `a2a.server.push_notifier` | Webhook delivery for push notifications |
| `A2AClient` | `a2a.client` | Client for calling remote A2A agents |

## Server Implementation

### Step 1: Implement AgentExecutor

```python
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Part, TextPart, Message, Role

class MyAgentExecutor(AgentExecutor):
    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Process incoming request and publish results."""
        # Extract user message from the request
        user_message = context.message
        user_text = ""
        if user_message and user_message.parts:
            for part in user_message.parts:
                if isinstance(part.root, TextPart):  # Pydantic discriminated union
                    user_text = part.root.text

        # Process the request (integrate with your LLM/logic here)
        result = await self._process(user_text)

        # Publish response as a message
        await event_queue.enqueue_event(
            Message(
                role=Role.agent,
                parts=[Part(root=TextPart(text=result))],
            )
        )

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Handle task cancellation."""
        pass

    async def _process(self, text: str) -> str:
        # Your agent logic here
        return f"Processed: {text}"
```

### Step 2: Define the Agent Card

```python
from a2a.types import AgentCard, AgentSkill, AgentCapabilities

agent_card = AgentCard(
    name="my-agent",
    description="An agent that processes text requests",
    url="http://localhost:9000",
    version="1.0.0",
    skills=[
        AgentSkill(
            id="text-processing",
            name="Text Processing",
            description="Processes text input and returns results",
            input_modes=["text/plain"],
            output_modes=["text/plain"],
        )
    ],
    capabilities=AgentCapabilities(
        streaming=True,
        push_notifications=False,
    ),
)
```

### Step 3: Create and Run the Server

```python
from a2a.server.request_handler import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication
import uvicorn

executor = MyAgentExecutor()
handler = DefaultRequestHandler(
    agent_executor=executor,
    task_store=InMemoryTaskStore(),
)

app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=handler,
)

uvicorn.run(app.build(), host="0.0.0.0", port=9000)
```

The server automatically exposes:
- `GET /.well-known/agent-card.json` -- agent discovery
- `POST /` -- JSON-RPC endpoint for all operations

## Client Usage

### Discover and Call an Agent

```python
from a2a.client import A2AClient
from a2a.types import (
    MessageSendParams,
    Message,
    Part,
    TextPart,
    Role,
)

async def call_agent():
    # Create client from agent URL (auto-discovers agent card)
    async with A2AClient(url="http://localhost:9000") as client:
        # Fetch the agent card
        card = await client.get_agent_card()
        print(f"Connected to: {card.name}")

        # Send a message
        request = MessageSendParams(
            message=Message(
                role=Role.user,
                parts=[Part(root=TextPart(text="Hello, agent!"))],
            )
        )
        response = await client.send_message(request)
        print(response)
```

### Poll for Task Completion

```python
import asyncio
from a2a.types import TaskState

async def poll_task(client: A2AClient, task_id: str):
    while True:
        task = await client.get_task(task_id)
        if task.status.state in (
            TaskState.completed,
            TaskState.failed,
            TaskState.canceled,
        ):
            return task
        await asyncio.sleep(1)
```

## Streaming (SSE)

### Server-Side Streaming

The executor publishes events incrementally via the `EventQueue`. The framework handles SSE transport automatically when the client uses `SendStreamingMessage`.

```python
class StreamingExecutor(AgentExecutor):
    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        # Stream partial results
        for chunk in await self._process_streaming(context.message):
            await event_queue.enqueue_event(
                Message(
                    role=Role.agent,
                    parts=[Part(root=TextPart(text=chunk))],
                )
            )
```

### Client-Side Streaming

```python
async def stream_from_agent(client: A2AClient):
    request = MessageSendParams(
        message=Message(
            role=Role.user,
            parts=[Part(root=TextPart(text="Generate a report"))],
        )
    )
    async for event in client.send_streaming_message(request):
        print(event)
```

## Push Notifications

For long-running tasks where the client cannot maintain a persistent connection.

### Server Setup

```python
from a2a.server.push_notifier import PushNotifier

notifier = PushNotifier()

handler = DefaultRequestHandler(
    agent_executor=executor,
    task_store=InMemoryTaskStore(),
    push_notifier=notifier,
)

# Declare push notification support in the agent card
agent_card = AgentCard(
    # ...
    capabilities=AgentCapabilities(push_notifications=True),
)
```

### Client Registration

```python
from a2a.types import PushNotificationConfig

# Register a webhook callback
config = PushNotificationConfig(
    url="https://my-app.example.com/webhook",
    task_id=task_id,
)
await client.set_push_notification_config(config)
```

## Task Lifecycle

Tasks transition through states managed by the framework:

```
created -> working -> completed
                  \-> failed
                  \-> canceled
                  \-> rejected
                  \-> input_required (awaiting user input)
                  \-> auth_required (awaiting auth)
```

The `DefaultRequestHandler` manages state transitions automatically. The executor signals completion by:
- Publishing a final `Message` -- task completes
- Raising an exception -- task fails
- Responding to `cancel()` -- task cancels

## Structured Data

Use `DataPart` for structured JSON payloads:

```python
from a2a.types import DataPart

await event_queue.enqueue_event(
    Message(
        role=Role.agent,
        parts=[
            Part(root=DataPart(data={"result": 42, "confidence": 0.95})),
        ],
    )
)
```

## Artifacts

Publish tangible deliverables as artifacts:

```python
from a2a.types import Artifact, TextPart

await event_queue.enqueue_event(
    Artifact(
        name="report.md",
        parts=[Part(root=TextPart(text="# Generated Report\n\n..."))],
    )
)
```

## Testing with Mokksy

Mokksy provides mock A2A servers for testing client code:

```python
import pytest
from a2a.client import A2AClient

@pytest.fixture
async def mock_server():
    # Start a Mokksy mock server with predefined responses
    # See https://github.com/a2aproject/a2a-python for Mokksy docs
    ...

async def test_client_integration(mock_server):
    async with A2AClient(url=mock_server.url) as client:
        card = await client.get_agent_card()
        assert card.name == "mock-agent"
```

## Production Persistence

Replace `InMemoryTaskStore` with a SQL-backed store:

```python
from a2a.server.tasks import PostgreSQLTaskStore  # or MySQLTaskStore, SQLiteTaskStore

task_store = PostgreSQLTaskStore(connection_string="postgresql://...")
handler = DefaultRequestHandler(
    agent_executor=executor,
    task_store=task_store,
)
```

## Resources

- [Python SDK repo](https://github.com/a2aproject/a2a-python)
- [Python API docs](https://a2a-protocol.org/latest/sdk/python/api/)
- [Sample agents](https://github.com/a2aproject/a2a-samples)
