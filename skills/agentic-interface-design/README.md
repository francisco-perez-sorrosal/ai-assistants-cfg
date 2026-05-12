# agentic-interface-design

Interface design craft for the model as consumer — MCP tools, function-calling schemas, agent-to-agent contracts.

## When to Use

Activate this skill when:

- Designing or reviewing MCP tools — names, descriptions, parameter schemas
- Deciding fat-vs-thin tool decomposition or when to use progressive disclosure
- Designing error responses that enable model self-recovery
- Evaluating whether a tool surface exceeds ~20–25 tools (degradation threshold)
- Designing idempotency for tools with side effects
- Structuring tool result pagination and response size
- Designing JSON schemas for function-calling tools
- Designing A2A contracts (Agent Cards, task terminal states)

## Activation

The skill activates on agentic/MCP/tool design vocabulary: "MCP tool", "tool design", "tool description", "function calling", "agent tool", "tool schema", "fat tool", "progressive disclosure", "agentic interface", "A2A contract", "agent error", "idempotency key".

## Skill Contents

| File | Purpose |
|------|---------|
| `SKILL.md` | Core principles: names-as-interface, human-vs-agent ergonomics table, fat-vs-thin rule, token economy numbers, error grammar, pagination rules |
| `references/design-fundamentals.md` | Shared design canon (Rams, Norman, Nielsen, Bloch) — load for first-principles grounding. **Byte-identical** across all four interface-design skills (intentional; sentinel will flag as redundancy — it is correct). |
| `references/tool-design-for-models.md` | Tool naming, description writing, parameter naming, granularity decisions |
| `references/mcp-primitives-as-design-surfaces.md` | When to use tool vs. resource vs. prompt; the do-not-mix rule |
| `references/agent-error-ergonomics.md` | Error grammar, idempotency patterns, Stripe-style request_id |
| `references/progressive-disclosure-of-tools.md` | Token economy problem, meta-tool pattern, domain bundles, 85–100× reduction |
| `references/agent-contracts.md` | JSON schema design, structured vs. prose, pagination, A2A design |
| `references/design-review-checklist.md` | Audit checklist for MCP servers, tool surfaces, A2A contracts |

## Related Skills

- **`mcp-crafting`** — How to build an MCP server (implementation mechanics). This skill covers how *good* the design is; `mcp-crafting` covers how to build it.
- **`agentic-sdks`** — SDK loop mechanics (wiring tools to an agent loop, framework selection). This skill covers tool design craft; `agentic-sdks` covers SDK mechanics.
- **`communicating-agents`** — A2A protocol mechanics (Agent Cards, task lifecycle). This skill covers A2A contract design; `communicating-agents` covers the protocol.
- **`api-design-craft`** — Sibling hat: the same quality/taste lens for REST/GraphQL/gRPC APIs.
- **`llm-prompt-engineering`** — When a tool description is long enough to be a mini-prompt.
