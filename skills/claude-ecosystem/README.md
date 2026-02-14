# claude-ecosystem

Anthropic Claude platform knowledge -- models, API features, SDKs, and documentation navigation.

## Contents

| File | Purpose |
| --- | --- |
| `SKILL.md` | Core ecosystem map: model lineup, API feature index, SDK quick reference |
| `references/api-features.md` | Detailed API feature coverage with usage patterns and availability |
| `references/sdk-patterns.md` | Python/TS SDK idioms, async patterns, error handling, Agent SDK |
| `references/docs-map.md` | Documentation site navigation, repo index, quick lookup guide |
| `references/platform-services.md` | Batch processing, prompt caching, Files API, cost optimization |

## Activation

The skill activates automatically when the agent detects tasks related to:

- Claude API usage (Messages API, tool use, extended thinking, structured outputs)
- Model selection (comparing Opus, Sonnet, Haiku capabilities)
- Anthropic SDK integration (Python SDK, TypeScript SDK, Agent SDK)
- Platform services (prompt caching, batch processing, Files API)
- Navigating Anthropic documentation or finding the right GitHub repo

Trigger explicitly by asking about "Claude API," "Anthropic SDK," "model selection," or referencing this skill by name.

## When to Use

- Choosing between Claude models for a task
- Using Claude Messages API features (tool use, extended thinking, caching, structured outputs)
- Integrating Anthropic SDKs (Python, TypeScript, Agent SDK)
- Finding the right Anthropic documentation or GitHub repo
- Optimizing cost with batches, caching, or model selection

## Related Skills

- [`mcp-crafting`](../mcp-crafting/) -- Building MCP servers (transports, tools, resources)
- [`python-development`](../python-development/) -- General Python patterns and tooling
