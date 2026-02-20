# A2A Protocol -- TypeScript SDK

TypeScript-specific implementation guide. Load alongside the generic [Communicating Agents](../SKILL.md) skill.

## Setup

```bash
npm install @a2a-js/sdk
# Express for HTTP server
npm install express @types/express
# Optional: gRPC support
npm install @grpc/grpc-js @bufbuild/protobuf
```

## Module Exports

| Import Path | Contents |
|-------------|----------|
| `@a2a-js/sdk` | Types and interfaces |
| `@a2a-js/sdk/server` | Server utilities |
| `@a2a-js/sdk/server/express` | Express middleware |
| `@a2a-js/sdk/server/grpc` | gRPC service |
| `@a2a-js/sdk/client` | Client classes |
| `@a2a-js/sdk/client/grpc` | gRPC client transport |

## Core Classes

| Class | Module | Purpose |
|-------|--------|---------|
| `AgentExecutor` | `@a2a-js/sdk/server` | Abstract base -- implement `execute()` and `cancelTask()` |
| `DefaultRequestHandler` | `@a2a-js/sdk/server` | Routes JSON-RPC requests to executor |
| `InMemoryTaskStore` | `@a2a-js/sdk/server` | Dev-only task persistence |
| `ExecutionEventBus` | `@a2a-js/sdk/server` | Publish messages, artifacts, status updates |
| `ClientFactory` | `@a2a-js/sdk/client` | Creates clients from agent URLs, auto-discovers transports |
| `GrpcTransportFactory` | `@a2a-js/sdk/client/grpc` | Explicit gRPC transport |

**Express middleware functions:**

| Function | Purpose |
|----------|---------|
| `agentCardHandler(card)` | `GET /.well-known/agent-card.json` |
| `jsonRpcHandler(handler)` | `POST /` JSON-RPC endpoint |
| `restHandler(handler)` | REST-style endpoints |
| `grpcService(handler)` | gRPC service definition |

## Server Implementation

### Step 1: Implement AgentExecutor

```typescript
import {
  AgentExecutor,
  ExecutionEventBus,
  RequestContext,
} from '@a2a-js/sdk/server';
import { Message, Part, Role, TaskState } from '@a2a-js/sdk';

class MyAgentExecutor implements AgentExecutor {
  async execute(
    requestContext: RequestContext,
    eventBus: ExecutionEventBus
  ): Promise<void> {
    // Extract user message
    const userMessage = requestContext.message;
    const userText = userMessage?.parts
      ?.filter((p): p is Part & { text: string } => 'text' in p)
      .map((p) => p.text)
      .join('');

    // Process the request (integrate with your LLM/logic)
    const result = await this.process(userText ?? '');

    // Publish response
    eventBus.publish({
      kind: 'message',
      message: {
        role: Role.Agent,
        parts: [{ text: result }],
      },
    });
  }

  async cancelTask(
    requestContext: RequestContext,
    eventBus: ExecutionEventBus
  ): Promise<void> {
    // Handle cancellation
  }

  private async process(text: string): Promise<string> {
    return `Processed: ${text}`;
  }
}
```

### Step 2: Define the Agent Card

```typescript
import { AgentCard } from '@a2a-js/sdk';

const agentCard: AgentCard = {
  name: 'my-agent',
  description: 'An agent that processes text requests',
  url: 'http://localhost:9000',
  version: '1.0.0',
  skills: [
    {
      id: 'text-processing',
      name: 'Text Processing',
      description: 'Processes text input and returns results',
      inputModes: ['text/plain'],
      outputModes: ['text/plain'],
    },
  ],
  capabilities: {
    streaming: true,
    pushNotifications: false,
  },
};
```

### Step 3: Create and Run the Server

```typescript
import express from 'express';
import {
  DefaultRequestHandler,
  InMemoryTaskStore,
} from '@a2a-js/sdk/server';
import {
  agentCardHandler,
  jsonRpcHandler,
} from '@a2a-js/sdk/server/express';

const executor = new MyAgentExecutor();
const handler = new DefaultRequestHandler({
  agentExecutor: executor,
  taskStore: new InMemoryTaskStore(),
});

const app = express();
app.use(express.json());

// Mount A2A endpoints
app.get('/.well-known/agent-card.json', agentCardHandler(agentCard));
app.post('/', jsonRpcHandler(handler));

app.listen(9000, () => {
  console.log('A2A server running on port 9000');
});
```

## Client Usage

### Discover and Call an Agent

```typescript
import { ClientFactory } from '@a2a-js/sdk/client';
import { Message, Part, Role } from '@a2a-js/sdk';

async function callAgent() {
  // Create client from agent URL (auto-discovers agent card and transports)
  const client = await ClientFactory.create('http://localhost:9000');

  // Fetch agent card
  const card = await client.getAgentCard();
  console.log(`Connected to: ${card.name}`);

  // Send a message
  const response = await client.sendMessage({
    message: {
      role: Role.User,
      parts: [{ text: 'Hello, agent!' }],
    },
  });
  console.log(response);
}
```

### Poll for Task Completion

```typescript
import { TaskState } from '@a2a-js/sdk';

async function pollTask(client: Awaited<ReturnType<typeof ClientFactory.create>>, taskId: string) {
  const terminalStates = new Set([
    TaskState.Completed,
    TaskState.Failed,
    TaskState.Canceled,
  ]);

  while (true) {
    const task = await client.getTask(taskId);
    if (terminalStates.has(task.status.state)) {
      return task;
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
}
```

## Streaming (SSE)

### Server-Side Streaming

Publish events incrementally via the `ExecutionEventBus`. The framework handles SSE transport when the client uses `SendStreamingMessage`.

```typescript
class StreamingExecutor implements AgentExecutor {
  async execute(
    requestContext: RequestContext,
    eventBus: ExecutionEventBus
  ): Promise<void> {
    for await (const chunk of this.processStreaming(requestContext.message)) {
      eventBus.publish({
        kind: 'message',
        message: {
          role: Role.Agent,
          parts: [{ text: chunk }],
        },
      });
    }
  }

  async cancelTask(
    requestContext: RequestContext,
    eventBus: ExecutionEventBus
  ): Promise<void> {}

  private async *processStreaming(message: Message | undefined) {
    // Your streaming logic here
    yield 'Processing...';
    yield 'Done.';
  }
}
```

### Client-Side Streaming

```typescript
async function streamFromAgent(client: Awaited<ReturnType<typeof ClientFactory.create>>) {
  const stream = client.sendStreamingMessage({
    message: {
      role: Role.User,
      parts: [{ text: 'Generate a report' }],
    },
  });

  for await (const event of stream) {
    console.log(event);
  }
}
```

## Task and Artifact Handling

### Structured Data

```typescript
eventBus.publish({
  kind: 'message',
  message: {
    role: Role.Agent,
    parts: [{ data: { result: 42, confidence: 0.95 } }],
  },
});
```

### Artifacts

Publish tangible deliverables:

```typescript
eventBus.publish({
  kind: 'artifact',
  artifact: {
    name: 'report.md',
    parts: [{ text: '# Generated Report\n\n...' }],
  },
});
```

## gRPC Transport

### Server

```typescript
import { grpcService } from '@a2a-js/sdk/server/grpc';

const service = grpcService(handler);
// Mount on a gRPC server
```

### Client

```typescript
import { GrpcTransportFactory } from '@a2a-js/sdk/client/grpc';

const client = await ClientFactory.create('http://localhost:9000', {
  transportFactory: new GrpcTransportFactory(),
});
```

## REST Endpoints

Mount REST-style endpoints alongside JSON-RPC:

```typescript
import { restHandler } from '@a2a-js/sdk/server/express';

app.use('/api', restHandler(handler));
// Exposes: GET /api/tasks/:id, POST /api/messages, etc.
```

## Resources

- [JS/TS SDK repo](https://github.com/a2aproject/a2a-js)
- [Sample agents](https://github.com/a2aproject/a2a-samples)
