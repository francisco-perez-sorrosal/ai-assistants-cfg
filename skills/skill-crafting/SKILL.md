---
description: Creating, updating, and optimizing Agent Skills for Claude Code, Cursor, and other compatible agents. Covers activation patterns, content structure, progressive disclosure, and development workflows. Use when creating new skills, updating or modernizing existing skills, converting memory files to skills, debugging skill activation, or understanding skill architecture and best practices.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, WebFetch(domain:agentskills.io), WebFetch(domain:platform.claude.com)]
---

# Agent Skills Development

Reference for developing effective Agent Skills. Official specification at [agentskills.io](https://agentskills.io). Authoring guidance at [Anthropic's best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).

**Satellite files** (loaded on-demand):

- [references/cross-agent-portability.md](references/cross-agent-portability.md) -- discovery paths per tool, portability guidance
- [references/artifact-naming.md](references/artifact-naming.md) -- naming conventions for all artifact types (skills, agents, commands, rules)
- [references/content-and-development.md](references/content-and-development.md) -- content type selection, feedback loops, evaluation-driven development, executable code practices
- [references/patterns-and-troubleshooting.md](references/patterns-and-troubleshooting.md) -- skill type patterns (read-only, script-based, template-based), anti-patterns, troubleshooting

## Core Principles

**The context window is a public good.** Your skill shares it with system prompts, conversation history, other skills' metadata, and the user's request. Every token must earn its place.

**The agent is already smart.** Only include information the model doesn't possess. Challenge each piece: "Does the agent really need this?" If in doubt, leave it out.

**But not all agents are equally capable.** Skills may be consumed by agents with varying model capabilities. Avoid explaining universal knowledge (basic syntax, common idioms), but do include enough context — concrete examples, complete workflows, and explicit decision criteria — so your specific conventions can be followed correctly by less capable agents too. Examples and workflows are robust across the capability spectrum: they guide weaker agents without burdening stronger ones.

**Conciseness**: Aim to keep `SKILL.md` concise (500 lines is a good guideline, not a hard limit). Use progressive disclosure — split detailed content into separate files loaded on-demand. Remember that once your skill is activated, its tokens compete for attention with other skills' metadata, the system prompt, and conversation history. Every instruction you add dilutes the weight of every other instruction — in your skill and in others.

**Appropriate Degrees of Freedom**: Match specificity to the task's fragility:

- **High freedom** (text instructions): Multiple valid approaches, context-dependent decisions
- **Medium freedom** (pseudocode/parameterized scripts): Preferred pattern exists, some variation acceptable
- **Low freedom** (exact scripts, no parameters): Fragile operations where consistency is critical

Think of it as a path: an open field (many valid routes, give general direction) vs. a narrow bridge over a cliff (one safe way, provide exact guardrails).

## Specification

### Frontmatter (required)

```yaml
---
description: What the skill does and when to use it. Include specific trigger terms.
---
```

Optional fields:

```yaml
---
name: pdf-processing
description: Extract text and tables from PDF files, fill forms, merge documents.
license: Apache-2.0
compatibility: Requires git, docker, and internet access
metadata:
  author: example-org
  version: "1.0"
allowed-tools: [Read, Write, Bash]
---
```

| Field           | Required | Constraints                                                              |
| --------------- | -------- | ------------------------------------------------------------------------ |
| `name`          | No       | 1-64 chars. Lowercase alphanumeric + hyphens. Claude Code infers from directory name; omit to avoid plugin install conflicts. |
| `description`   | Yes      | 1-1024 chars. What it does + when to use it + trigger terms.             |
| `license`       | No       | License name or reference to bundled file.                               |
| `compatibility` | No       | Max 500 chars. Environment requirements.                                 |
| `metadata`      | No       | Arbitrary key-value pairs for additional info.                           |
| `allowed-tools` | No       | Pre-approved tools the skill may use. (Experimental)                     |

### Directory Name Constraints

The directory name is the skill's identity (Claude Code infers the name from it):

- Lowercase letters, numbers, and hyphens only
- No consecutive hyphens (`--`), no leading/trailing hyphens
- If `name` field is present, it must match the directory name
- Prefer gerund form (`processing-pdfs`) or noun phrases (`pdf-processing`)
- Avoid vague names: `helper`, `utils`, `tools`

### Description Best Practices

Write in third person — the description is injected into the system prompt.

- "Extracts text from PDF files, fills forms, merges documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction."
- Not: "I can help you process PDFs..."
- Not: "You can use this to process PDFs..."
- Not: "Helps with documents."

Include: what the skill does, specific trigger terms, key use cases.

## Skill Structure

### Directory Layout

```
skill-name/
├── SKILL.md              # Required: instructions + metadata
├── README.md             # Recommended: overview, usage guide, skill contents
├── scripts/              # Optional: executable utilities
├── references/           # Optional: detailed docs loaded on-demand
└── assets/               # Optional: templates, schemas, data files
```

### README Section Order

READMEs are human-facing documentation (not loaded into Claude's context). Use this section order:

1. `## When to Use` — bullet list of scenarios (required)
2. `## Activation` — how the skill gets triggered (required)
3. `## Skill Contents` — table of files in the skill directory (required)
4. `## Quick Start` — minimal usage example (optional)
5. `## Testing` — how to verify the skill works (optional)
6. `## Related Skills` — cross-references to other skills (optional)

Meta-crafting skills (those governing an artifact type) may add an artifact catalog section after Skill Contents.

### SKILL.md Section Ordering

No prescribed section order — structure should follow the skill's content and domain. A python skill and a refactoring skill will naturally have different sections. Keep related concepts grouped and use progressive disclosure (satellite files) for depth.

Satellite files can live at the skill root (e.g., `REFERENCE.md`, `pixi.md`) or inside subdirectories (e.g., `references/patterns.md`). Both conventions are valid. A common guideline: use root-level files when there are only one or two satellites; use subdirectories when there are three or more to keep the directory tidy.

### Progressive Disclosure

Three tiers of context loading:

1. **Metadata** (~100 tokens): `name` + `description` loaded at startup for all skills
2. **Instructions** (<5000 tokens recommended): Full `SKILL.md` body loaded on activation
3. **Resources** (as needed): Referenced files loaded only when required

### Storage Locations

- **Personal**: `~/.claude/skills/` (user-specific)
- **Project**: `.claude/skills/` (shared via git)

### File References

Keep one level deep from `SKILL.md`. Avoid nested reference chains — agents may partially read deeply nested files.

For reference files over 100 lines, include a table of contents at the top so the agent can see scope even with partial reads.

## Content Guidelines

**Consistent Terminology**: Choose one term per concept. Always "API endpoint," not mixing with "URL," "route," or "path."

**Examples Over Description**: Provide input/output pairs showing desired style and detail level -- more effective than prose descriptions alone.

**Templates**: Match strictness to requirements (strict = "ALWAYS use this exact template", flexible = "sensible default, adapt as needed").

**Avoid Time-Sensitive Info**: Use "Old Patterns" sections with `<details>` for deprecated methods rather than date-based conditionals.

Choose content type by degree of freedom: **scripts** for deterministic operations, **worked examples** for pattern matching, **prose instructions** for judgment calls. Include validation loops for complex tasks.

--> See [references/content-and-development.md](references/content-and-development.md) for the content type decision table, feedback loop patterns, and executable code best practices.

## Development Workflow

Start with a minimal SKILL.md addressing only observed gaps. Build evaluations (at least three test scenarios) BEFORE writing extensive documentation. Use the author-tester workflow: one instance writes, another tests in a fresh session.

--> See [references/content-and-development.md](references/content-and-development.md#evaluation-driven-development) for the full evaluation-driven development process, author-tester workflow, and navigation pattern observation guide.

## Executable Code Best Practices

Handle errors explicitly (don't punt to the agent), justify all constants, distinguish execution vs. reference intent, list package dependencies, and use fully qualified MCP tool names (`ServerName:tool_name`).

--> See [references/content-and-development.md](references/content-and-development.md#executable-code-best-practices) for detailed guidance and examples.

## Common Patterns

Three main skill types: **read-only reference** (`allowed-tools: [Read, Grep, Glob]`), **script-based** (`[Read, Bash, Write]`), and **template-based** (`[Read, Write, Edit]`).

--> See [references/patterns-and-troubleshooting.md](references/patterns-and-troubleshooting.md) for pattern details and `allowed-tools` configurations.

## Anti-Patterns

--> See [references/patterns-and-troubleshooting.md](references/patterns-and-troubleshooting.md#anti-patterns) for the full list of anti-patterns to avoid (vague descriptions, over-explaining, deeply nested references, hard-referencing slash commands, etc.).

## Troubleshooting

--> See [references/patterns-and-troubleshooting.md](references/patterns-and-troubleshooting.md#troubleshooting) for solutions to skill activation, YAML parsing, and path issues.

## Checklist

Before deploying a skill:

**Core Quality**

- [ ] Third-person description with specific trigger terms (what + when)
- [ ] If `name` is present, it matches directory name (lowercase, hyphens only)
- [ ] `README.md` with overview, activation triggers, and skill contents table
- [ ] `SKILL.md` is concise (aim for ~500 lines, use progressive disclosure for longer content)
- [ ] One-level-deep file references
- [ ] Consistent terminology throughout
- [ ] Concrete examples provided
- [ ] Progressive disclosure (metadata -> instructions -> resources)
- [ ] No time-sensitive information
- [ ] Clear workflows with steps and feedback loops

**Code & Scripts** (if applicable)

- [ ] Scripts handle errors explicitly (solve, don't punt)
- [ ] No voodoo constants — all values justified
- [ ] Required packages listed and verified
- [ ] Forward slashes in all paths
- [ ] Validation/verification for critical operations

**Testing**

- [ ] At least three evaluation scenarios created
- [ ] Tested across target models
- [ ] Real-world scenario validation

## Cross-Agent Portability

The [Agent Skills standard](https://agentskills.io) is adopted by 25+ tools including Claude Code, Cursor, VS Code/Copilot, OpenAI Codex, Gemini CLI, Roo Code, Goose, Amp, and others. A well-authored SKILL.md works across all of them.

**What's portable**: The SKILL.md format (frontmatter + markdown body), directory structure (`scripts/`, `references/`, `assets/`), and progressive disclosure model.

**What's tool-specific**: `allowed-tools` names, MCP tool references (`ServerName:tool_name`), `compatibility` field values, and tool-specific frontmatter extensions (e.g., Claude Code's `context: fork`, `disable-model-invocation`).

To maximize portability, keep the SKILL.md body in standard markdown and isolate tool-specific instructions behind clear headings. See [references/cross-agent-portability.md](references/cross-agent-portability.md) for discovery paths per tool, the relationship between skills and project instruction files (`AGENTS.md`, `CLAUDE.md`), and detailed guidance.

## Resources

- [Agent Skills Specification](https://agentskills.io/specification)
- [Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Example Skills](https://github.com/anthropics/skills) — Anthropic's official reference implementations
- [Validation Library (skills-ref)](https://github.com/agentskills/agentskills/tree/main/skills-ref)
- [Awesome Agent Skills](https://github.com/VoltAgent/awesome-agent-skills) — Curated collection of 200+ skills from Anthropic, Google Labs, Vercel, Stripe, Cloudflare, and others
- [Vercel Labs Skills](https://github.com/vercel-labs/agent-skills) — Reference implementations from Vercel
- [Claude Skills Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/) — Lee Han Chung's architectural analysis of how skills work
- [Agent Skills Course](https://www.deeplearning.ai/short-courses/agent-skills-with-anthropic/) — DeepLearning.AI hands-on course on skill creation
