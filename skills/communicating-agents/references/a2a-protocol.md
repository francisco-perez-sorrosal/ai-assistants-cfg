# A2A Protocol Reference

Complete protocol reference for the A2A (Agent2Agent) specification. Load alongside the [Communicating Agents](../SKILL.md) skill.

- **Current version**: v0.3.0 (July 30, 2025)
- **Governance**: Linux Foundation, 150+ supporting organizations
- **Spec**: [a2a-protocol.org/latest/specification/](https://a2a-protocol.org/latest/specification/)
- **Repo**: [github.com/a2aproject/A2A](https://github.com/a2aproject/A2A)

## Architecture -- Three Layers

### Layer 1: Data Model (Protocol Buffers)

Defines the types exchanged between agents.

### Layer 2: Abstract Operations

Defines 11 operations independent of transport.

### Layer 3: Protocol Bindings

Maps operations to transport protocols:
- **JSON-RPC 2.0** -- primary binding over HTTP
- **gRPC** -- added in v0.3 for high-throughput scenarios
- **HTTP+JSON/REST** -- simplified REST-style access

## Data Model

### Task

Stateful work unit -- the central object in A2A interactions.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique task identifier |
| `contextId` | string | Server-generated, groups related tasks |
| `status` | TaskStatus | Current state and metadata |
| `history` | Message[] | Conversation history |
| `artifacts` | Artifact[] | Output deliverables |
| `metadata` | map | Arbitrary key-value pairs |

### TaskStatus

| Field | Type | Description |
|-------|------|-------------|
| `state` | TaskState | Current lifecycle state |
| `message` | Message | Optional status message |
| `timestamp` | string | ISO 8601 timestamp |

### TaskState (Lifecycle)

```
created --> working --> completed
                   \--> failed
                   \--> canceled
                   \--> rejected
                   \--> input_required
                   \--> auth_required
```

| State | Description |
|-------|-------------|
| `created` | Task received, not yet processing |
| `working` | Actively processing |
| `completed` | Successfully finished |
| `failed` | Encountered an error |
| `canceled` | Canceled by client request |
| `rejected` | Server refused the task |
| `input_required` | Awaiting additional user input |
| `auth_required` | Awaiting authentication/authorization |

**Interruption states** (`input_required`, `auth_required`) allow multi-turn interactions. The client sends additional messages to resume processing.

### Message

Single communication turn between actors.

| Field | Type | Description |
|-------|------|-------------|
| `role` | Role | `user` or `agent` |
| `parts` | Part[] | Content containers |
| `metadata` | map | Arbitrary key-value pairs |

### Part

Content container using a union (oneof) pattern:

| Variant | Fields | Description |
|---------|--------|-------------|
| `TextPart` | `text: string` | Plain text content |
| `DataPart` | `data: object` | Structured JSON data |
| `RawPart` | `bytes: bytes` | Raw binary content |
| `UrlPart` | `url: string` | URI reference |

**Common fields** (all variants): `mediaType` (optional MIME type), `filename` (optional), `metadata` (optional key-value pairs).

### Artifact

Tangible deliverable output from task processing.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Human-readable artifact name |
| `parts` | Part[] | Artifact content |
| `metadata` | map | Arbitrary key-value pairs |

### AgentCard

JSON metadata document for agent discovery.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Human-readable agent name |
| `description` | string | Yes | What the agent does |
| `url` | string | Yes | Service endpoint URL |
| `version` | string | Yes | Agent version |
| `provider` | Provider | No | Organization info (name, url) |
| `skills` | AgentSkill[] | No | Capabilities the agent offers |
| `capabilities` | AgentCapabilities | No | Supported features |
| `schemes` | AuthScheme[] | No | Authentication requirements |
| `defaultInputModes` | string[] | No | Accepted input MIME types |
| `defaultOutputModes` | string[] | No | Produced output MIME types |

### AgentSkill

Describes a specific capability within an agent.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique skill identifier |
| `name` | string | Human-readable name |
| `description` | string | What the skill does |
| `inputModes` | string[] | Accepted MIME types |
| `outputModes` | string[] | Produced MIME types |
| `examples` | Example[] | Usage examples |

### AgentCapabilities

| Field | Type | Description |
|-------|------|-------------|
| `streaming` | boolean | Supports SSE streaming |
| `pushNotifications` | boolean | Supports webhook callbacks |
| `stateTransitionHistory` | boolean | Task history available |

### AuthScheme

| Field | Type | Description |
|-------|------|-------------|
| `scheme` | string | Auth type: `apiKey`, `bearer`, `oauth2`, `oidc`, `mtls`, `basic` |
| `in` | string | Where credentials go: `header`, `query` |
| `name` | string | Header/parameter name |
| `flows` | OAuthFlows | OAuth 2.0 flow config (when applicable) |

## Operations (11 Total)

### Message Operations

| Operation | Parameters | Returns | Description |
|-----------|-----------|---------|-------------|
| `SendMessage` | `MessageSendParams` | Task or Message | Send a message, receive task or immediate response |
| `SendStreamingMessage` | `MessageSendParams` | SSE stream | Send a message, receive streaming events |

**MessageSendParams:**

| Field | Type | Description |
|-------|------|-------------|
| `message` | Message | The message to send |
| `configuration` | MessageSendConfiguration | Optional settings |

**MessageSendConfiguration:**

| Field | Type | Description |
|-------|------|-------------|
| `acceptedOutputModes` | string[] | Preferred response formats |
| `pushNotificationConfig` | PushNotificationConfig | Webhook for async updates |
| `historyLength` | integer | Max history entries to include |
| `blocking` | boolean | Wait for completion vs. return immediately |

### Task Operations

| Operation | Parameters | Returns | Description |
|-----------|-----------|---------|-------------|
| `GetTask` | `task_id`, `history_length` | Task | Retrieve task state and history |
| `ListTasks` | `context_id`, `filters` | Task[] | List tasks in a context |
| `CancelTask` | `task_id` | Task | Request task cancellation |

### Subscription Operations

| Operation | Parameters | Returns | Description |
|-----------|-----------|---------|-------------|
| `SubscribeToTask` | `task_id` | SSE stream | Subscribe to task updates via streaming |

### Push Notification Operations

| Operation | Parameters | Returns | Description |
|-----------|-----------|---------|-------------|
| `SetPushNotificationConfig` | `PushNotificationConfig` | PushNotificationConfig | Register webhook callback |
| `GetPushNotificationConfig` | `task_id` | PushNotificationConfig | Get current webhook config |
| `DeletePushNotificationConfig` | `task_id` | void | Remove webhook registration |

**PushNotificationConfig:**

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Webhook callback URL |
| `task_id` | string | Task to monitor |
| `token` | string | Optional verification token |

### Discovery Operations

| Operation | Parameters | Returns | Description |
|-----------|-----------|---------|-------------|
| `GetExtendedAgentCard` | credentials | AgentCard | Authenticated agent card with sensitive metadata |

## Agent Discovery

### Well-Known URI (Primary)

Agents publish their Agent Card at a standard location:

```
GET https://{domain}/.well-known/agent-card.json
```

Per RFC 8615. No authentication required for the base card.

### Extended Agent Cards

Sensitive metadata (internal skills, restricted endpoints) exposed via authenticated `GetExtendedAgentCard` operation. The base card advertises the extended endpoint; clients authenticate to retrieve full details.

### Curated Registries

Centralized agent directories. Not yet standardized -- currently proprietary implementations. Expected to converge as the ecosystem matures.

### Direct Configuration

For closed networks or development:
- Hardcoded agent URLs
- Configuration files
- Environment variables
- Service mesh discovery

## Interaction Patterns

### Request/Response (Polling)

1. Client sends `SendMessage`
2. Server returns Task with `created` or `working` state
3. Client polls `GetTask` until terminal state

Best for: simple request-response, batch processing, clients that cannot maintain persistent connections.

### Streaming (SSE)

1. Client sends `SendStreamingMessage`
2. Server returns SSE stream with incremental events
3. Events include status updates, partial messages, artifacts
4. Stream closes on terminal state

Best for: real-time UIs, progressive output, long-running tasks with incremental results.

### Push Notifications

1. Client sends `SendMessage` with `PushNotificationConfig`
2. Server processes asynchronously
3. Server POSTs status updates to the webhook URL
4. Client retrieves final result via `GetTask`

Best for: very long-running tasks, fire-and-forget patterns, mobile/serverless clients.

## Authentication and Security

### Supported Schemes

| Scheme | Transport | Use Case |
|--------|-----------|----------|
| API Key | Header or query param | Simple service-to-service |
| HTTP Bearer | Authorization header | Token-based auth |
| OAuth 2.0 | Authorization header | Delegated access |
| OpenID Connect | Authorization header | Identity verification |
| Mutual TLS | TLS layer | High-security environments |
| HTTP Basic | Authorization header | Simple username/password |

### Security Requirements

- TLS 1.2+ required for all production deployments
- Agents maintain opacity -- they do not expose internal architecture
- Credentials passed via HTTP headers (never in URLs for sensitive tokens)
- Agent Cards declare required auth schemes -- clients must satisfy them before calling

## JSON-RPC Binding

A2A uses JSON-RPC 2.0 over HTTP as the primary protocol binding.

**Request format:**

```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{"text": "Hello"}]
    }
  },
  "id": "req-1"
}
```

**Method names:**

| Operation | JSON-RPC Method |
|-----------|-----------------|
| SendMessage | `message/send` |
| SendStreamingMessage | `message/stream` |
| GetTask | `tasks/get` |
| ListTasks | `tasks/list` |
| CancelTask | `tasks/cancel` |
| SubscribeToTask | `tasks/subscribe` |
| SetPushNotificationConfig | `tasks/pushNotificationConfig/set` |
| GetPushNotificationConfig | `tasks/pushNotificationConfig/get` |
| DeletePushNotificationConfig | `tasks/pushNotificationConfig/delete` |
| GetExtendedAgentCard | `agent/authenticatedExtendedCard` |

## Resources

- [Full specification](https://a2a-protocol.org/latest/specification/)
- [Key concepts](https://a2a-protocol.org/latest/topics/key-concepts/)
- [Agent discovery](https://a2a-protocol.org/latest/topics/agent-discovery/)
- [Protocol repo](https://github.com/a2aproject/A2A)
