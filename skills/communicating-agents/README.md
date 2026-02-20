# Communicating Agents

Agent-to-agent communication protocols for multi-agent interoperability. Currently focused on the A2A (Agent2Agent) protocol, with an extensible structure for future protocols.

## When to Use

- Building multi-agent systems that communicate across frameworks or organizations
- Exposing agents via A2A endpoints for external consumption
- Implementing agent discovery with Agent Cards
- Integrating A2A with AI frameworks (ADK, LangGraph, CrewAI, Pydantic AI)
- Choosing between agent communication protocols

## Activation

Triggers on: multi-agent communication, agent interoperability, A2A protocol, Agent Cards, agent discovery, agent-to-agent protocols, cross-framework agent collaboration.

## Structure

```
communicating-agents/
├── SKILL.md                              # Protocol overview, selection guidance, A2A summary
├── contexts/
│   ├── a2a-python.md                    # A2A Python SDK implementation guide
│   └── a2a-typescript.md               # A2A TypeScript SDK implementation guide
├── references/
│   ├── a2a-protocol.md                  # Full A2A protocol reference (spec, data model, operations)
│   └── a2a-framework-integrations.md    # Framework integration patterns
└── README.md
```

## Coverage

### Protocol-Agnostic (SKILL.md)

- Protocol landscape and selection guidance
- A2A core concepts (Agent Cards, Tasks, Messages, Parts, Artifacts)
- Interaction patterns (polling, streaming, push)
- Discovery and authentication
- SDK selection (Python vs TypeScript)
- Minimal server patterns for both languages

### Per-Language SDK (contexts/)

- Setup and installation
- Core classes with code examples
- Server and client implementation
- Streaming and push notifications
- Task lifecycle handling
- Testing and production patterns

### Deep-Dive Reference (references/)

- Complete A2A data model and all 11 operations
- Task lifecycle state machine
- Agent Card schema (all fields)
- JSON-RPC method mapping
- Framework integration patterns for 8+ frameworks

## Related Skills

- **[agentic-sdks](../agentic-sdks/)** -- Building agents with OpenAI Agents SDK or Claude Agent SDK (agent loops, tools, multi-agent orchestration within a single framework). Complementary: build an agent with agentic-sdks, then expose it via communicating-agents.
