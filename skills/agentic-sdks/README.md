# Agentic SDKs

Building production AI agents with the OpenAI Agents SDK and Claude Agent SDK. Framework-agnostic patterns with language-specific implementation guides.

## Structure

```
agentic-sdks/
├── SKILL.md                              # Generic skill (loaded on activation)
├── contexts/
│   ├── openai-agents-python.md           # OpenAI Agents SDK for Python
│   ├── openai-agents-typescript.md       # OpenAI Agents SDK for TypeScript
│   ├── claude-agent-python.md            # Claude Agent SDK for Python
│   └── claude-agent-typescript.md        # Claude Agent SDK for TypeScript
├── references/
│   ├── openai-agents.md                  # Full OpenAI Agents SDK reference
│   └── claude-agent.md                   # Full Claude Agent SDK reference
└── README.md
```

## Related Skills

- **[claude-ecosystem](../claude-ecosystem/)** -- Claude API and Messages SDK patterns (model selection, API features). For Agent SDK implementation, use this skill instead.

## Coverage

### Framework-Agnostic (SKILL.md)

- Framework selection guidance
- Architecture comparison table
- Common agent patterns (triage, pipeline, fan-out, human-in-the-loop)
- Tool integration patterns
- Safety pattern comparison

### Per-Framework + Language (contexts/)

- Setup and installation
- Core abstractions with code examples
- Tool definition patterns
- Multi-agent orchestration
- Safety and guardrails
- Session management
- MCP integration
- Error handling
- Common pitfalls

### Deep-Dive Reference (references/)

- Full API surface documentation
- All configuration parameters
- Advanced patterns and edge cases
- Deployment and observability
