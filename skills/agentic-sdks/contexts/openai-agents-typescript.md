# OpenAI Agents SDK -- TypeScript

TypeScript-specific implementation guide. Load alongside the generic [Agentic SDKs](../SKILL.md) skill.

## Setup

```bash
npm install @openai/agents zod
```

Requires Node.js 22+, Deno, or Bun. Zod v4 required for schema validation. Set `OPENAI_API_KEY` environment variable.

## Core Abstractions

### Agent

```typescript
import { Agent } from '@openai/agents';

const agent = new Agent({
  name: 'Assistant',
  instructions: 'You are a helpful assistant.',
  tools: [myTool],
  handoffs: [otherAgent],
  outputType: myZodSchema,
});
```

**Use `Agent.create()` for proper type inference with handoffs:**

```typescript
const agent = Agent.create({
  name: 'Router',
  instructions: 'Route requests to specialists.',
  handoffs: [billingAgent, supportAgent],
});
```

### Running Agents

```typescript
import { run } from '@openai/agents';

const result = await run(agent, 'Your prompt');
console.log(result.finalOutput);
```

**Streaming:**

```typescript
const result = await run(agent, 'Your prompt', { stream: true });
for await (const event of result) {
  console.log(event);
}
```

## Tools

```typescript
import { z } from 'zod';
import { tool } from '@openai/agents';

const getWeather = tool({
  name: 'get_weather',
  description: 'Get the weather for a given city',
  parameters: z.object({
    city: z.string(),
    units: z.enum(['celsius', 'fahrenheit']).default('celsius'),
  }),
  execute: async (input) => {
    return `Weather in ${input.city}: sunny, 22${input.units === 'celsius' ? 'C' : 'F'}`;
  },
});

const agent = new Agent({
  name: 'Weather',
  instructions: 'Help with weather queries.',
  tools: [getWeather],
});
```

## Handoffs

```typescript
const billing = new Agent({
  name: 'Billing',
  instructions: 'Handle billing questions.',
  handoffDescription: 'Specialist for billing and payment issues',
});

const router = Agent.create({
  name: 'Router',
  instructions: 'Route to the right specialist.',
  handoffs: [billing],
});
```

## Guardrails

```typescript
import { Agent, inputGuardrail, outputGuardrail } from '@openai/agents';

const safetyGuardrail = inputGuardrail({
  name: 'safety_check',
  execute: async (ctx, input) => {
    const isSafe = !input.includes('dangerous');
    return { tripwireTriggered: !isSafe };
  },
});

const agent = new Agent({
  name: 'Safe Agent',
  inputGuardrails: [safetyGuardrail],
});
```

## Realtime Voice Agents

```typescript
import { RealtimeAgent, RealtimeSession, tool } from '@openai/agents-realtime';

const agent = new RealtimeAgent({
  name: 'Voice Assistant',
  instructions: 'Help users with voice queries.',
  tools: [getWeather],
});

const session = new RealtimeSession(agent);
await session.connect({ apiKey });
```

Install `@openai/agents-realtime` for voice support.

## MCP Integration

```typescript
import { Agent, run } from '@openai/agents';
import { MCPServerStdio } from '@openai/agents/mcp';

const server = new MCPServerStdio({
  command: 'npx',
  args: ['-y', '@modelcontextprotocol/server-filesystem', '/tmp'],
});

const agent = new Agent({
  name: 'File Agent',
  mcpServers: [server],
});

await server.connect();
try {
  const result = await run(agent, 'List files');
  console.log(result.finalOutput);
} finally {
  await server.close();
}
```

## Tracing

```typescript
import { trace } from '@openai/agents';

const span = trace('My workflow');
span.start();
try {
  const result = await run(agent, 'Step 1');
} finally {
  span.end();
}
```

Disable: `OPENAI_AGENTS_DISABLE_TRACING=1`.

## Error Handling

```typescript
import { MaxTurnsExceededError, GuardrailTripwireTriggered } from '@openai/agents';

try {
  const result = await run(agent, 'prompt', { maxTurns: 5 });
} catch (error) {
  if (error instanceof MaxTurnsExceededError) {
    console.log('Agent exceeded turn limit');
  } else if (error instanceof GuardrailTripwireTriggered) {
    console.log('Guardrail blocked execution');
  }
}
```

## Sessions and Context

The TypeScript SDK does not provide built-in session persistence (SQLiteSession/RedisSession) like the Python SDK. Use `result.toInputList()` for manual multi-turn management or server-managed conversations via `conversationId`.

Context sharing follows the same pattern as Python via generic type parameters, but TypeScript's type inference handles it automatically when using `Agent.create()`.

## Common Pitfalls

- Using `new Agent()` instead of `Agent.create()` when handoffs are present (loses type inference)
- Not installing Zod v4 -- the SDK validates schemas using Zod v4 API; v3 schemas fail at runtime
- Forgetting to call `server.connect()` / `server.close()` for MCP servers
- Not handling `MaxTurnsExceededError` for production agents
