---
name: agent-skills
description: Creating, updating, and optimizing Agent Skills for Claude Code, Cursor, and other compatible agents. Covers activation patterns, content structure, progressive disclosure, and development workflows. Use when creating new skills, updating or modernizing existing skills, converting memory files to skills, debugging skill activation, or understanding skill architecture and best practices.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, WebFetch(domain:agentskills.io), WebFetch(domain:platform.claude.com)]
---

# Agent Skills Development

Reference for developing effective Agent Skills. Official specification at [agentskills.io](https://agentskills.io). Authoring guidance at [Anthropic's best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).

## Core Principles

**The context window is a public good.** Your skill shares it with system prompts, conversation history, other skills' metadata, and the user's request. Every token must earn its place.

**The agent is already smart.** Only include information the model doesn't possess. Challenge each piece: "Does the agent really need this?" If in doubt, leave it out.

**Conciseness**: Aim to keep `SKILL.md` concise (500 lines is a good guideline, not a hard limit). Use progressive disclosure — split detailed content into separate files loaded on-demand.

**Appropriate Degrees of Freedom**: Match specificity to the task's fragility:

- **High freedom** (text instructions): Multiple valid approaches, context-dependent decisions
- **Medium freedom** (pseudocode/parameterized scripts): Preferred pattern exists, some variation acceptable
- **Low freedom** (exact scripts, no parameters): Fragile operations where consistency is critical

Think of it as a path: an open field (many valid routes, give general direction) vs. a narrow bridge over a cliff (one safe way, provide exact guardrails).

## Specification

### Frontmatter (required)

```yaml
---
name: my-skill-name
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
| `name`          | Yes      | 1-64 chars. Lowercase alphanumeric + hyphens. Must match directory name. |
| `description`   | Yes      | 1-1024 chars. What it does + when to use it + trigger terms.             |
| `license`       | No       | License name or reference to bundled file.                               |
| `compatibility` | No       | Max 500 chars. Environment requirements.                                 |
| `metadata`      | No       | Arbitrary key-value pairs for additional info.                           |
| `allowed-tools` | No       | Pre-approved tools the skill may use. (Experimental)                     |

### Name Constraints

- Lowercase letters, numbers, and hyphens only
- No consecutive hyphens (`--`), no leading/trailing hyphens
- Must match the parent directory name
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

**Examples Over Description**: Provide input/output pairs showing desired style and detail level — more effective than prose descriptions alone.

**Templates**: Match strictness to requirements:

- Strict: "ALWAYS use this exact template structure"
- Flexible: "Sensible default, adapt as needed"

**Avoid Time-Sensitive Info**: Use "Old Patterns" sections with `<details>` for deprecated methods rather than date-based conditionals.

### Workflows with Feedback Loops

For complex tasks, provide step-by-step checklists the agent can track:

```markdown
Task Progress:
- [ ] Step 1: Analyze inputs (run analyze.py)
- [ ] Step 2: Create mapping
- [ ] Step 3: Validate mapping (run validate.py)
- [ ] Step 4: Execute transformation
- [ ] Step 5: Verify output
```

Include validation loops: run validator -> fix errors -> repeat. This dramatically improves output quality.

For high-stakes operations, use the **plan-validate-execute** pattern: create a structured plan file, validate it with a script, then execute. Catches errors before they happen.

## Development Workflow

### Evaluation-Driven Development

Build evaluations BEFORE writing extensive documentation:

1. **Identify gaps**: Run the agent on representative tasks without the skill. Note specific failures
2. **Create evaluations**: Define three test scenarios covering those gaps
3. **Establish baseline**: Measure performance without the skill
4. **Write minimal instructions**: Just enough to address gaps and pass evaluations
5. **Iterate**: Execute evaluations, compare against baseline, refine

### Iterative Author-Tester Workflow

1. **Instance A** (author): Helps create/refine skill content
2. **Instance B** (tester): Uses the skill on real tasks in a fresh session
3. Observe Instance B's behavior — where it struggles, succeeds, or makes unexpected choices
4. Bring observations back to Instance A for refinements
5. Repeat until the skill reliably handles target scenarios

### Observe Navigation Patterns

Watch how the agent uses the skill:

- Unexpected file access order -> structure isn't intuitive
- Missed references -> links need to be more explicit
- Overreliance on one file -> content should be in `SKILL.md`
- Ignored files -> unnecessary or poorly signaled

## Executable Code Best Practices

**Solve, Don't Punt**: Handle error conditions explicitly rather than letting scripts fail for the agent to debug.

**Justify Constants**: Document why values exist — no voodoo numbers:

```python
# Three retries balances reliability vs speed
# Most intermittent failures resolve by second retry
MAX_RETRIES = 3
```

**Execution vs Reference**: Be explicit about intent:

- "Run `analyze_form.py` to extract fields" (execute)
- "See `analyze_form.py` for the extraction algorithm" (read as reference)

**Package Dependencies**: List required packages and verify availability.

**MCP Tool Names**: Use fully qualified format: `ServerName:tool_name`

## Common Patterns

### Read-Only Reference Skills

```yaml
allowed-tools: [Read, Grep, Glob]
```

For documentation and code analysis.

### Script-Based Skills

```yaml
allowed-tools: [Read, Bash, Write]
```

Reference scripts with forward slashes: `scripts/helper.py`

### Template-Based Skills

```yaml
allowed-tools: [Read, Write, Edit]
```

Store templates in `assets/` directory.

## Anti-Patterns

- Vague descriptions ("Helps with documents")
- Over-explaining what the agent already knows
- Windows-style paths — use forward slashes everywhere
- Too many options — provide one default with escape hatches
- Deeply nested references — keep one level from `SKILL.md`
- Scripts that punt errors to the agent
- Time-based conditionals
- Voodoo constants without justification
- Assuming tools/packages are installed without listing them

## Troubleshooting

### Skill Not Activating

1. Verify description includes specific trigger terms
2. Check YAML syntax (spaces not tabs, proper `---` delimiters)
3. Confirm `name` matches directory name exactly
4. Test with explicit trigger phrases
5. Consult the specific agent's documentation for skill-loading behavior

### YAML Errors

- Use spaces, never tabs
- Quote strings with special characters
- `---` delimiters on their own lines

### Path Issues

- Use forward slashes everywhere
- Verify referenced paths exist
- Use `~` for home directory in personal skills

## Checklist

Before deploying a skill:

**Core Quality**

- [ ] Third-person description with specific trigger terms (what + when)
- [ ] `name` matches directory name (lowercase, hyphens only)
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

## Resources

- [Agent Skills Specification](https://agentskills.io/specification)
- [Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Example Skills](https://github.com/anthropics/skills)
- [Validation Library (skills-ref)](https://github.com/agentskills/agentskills/tree/main/skills-ref)
