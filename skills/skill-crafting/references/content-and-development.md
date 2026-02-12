# Content Guidelines and Development Workflow

Detailed guidance on choosing content types, building workflows with feedback loops, and developing skills through evaluation-driven iteration. Reference material for the [Skill Creator](../SKILL.md) skill.

## Choosing Content Type

When deciding how to encode behavior in your skill, match the content type to the degree of freedom:

| Content Type | When to Use | Agent Behavior |
|---|---|---|
| **Script** (`scripts/`) | Deterministic operations where consistency is critical (validation, transformation, migration) | Executes the script -- doesn't generate its own |
| **Worked example** | A pattern exists that the agent should follow (commit format, report structure, API response shape) | Pattern-matches the example |
| **Prose instruction** | Multiple approaches are valid and context determines the best one (code review, architecture decisions) | Reasons about the situation |

Prefer scripts for anything a linter, formatter, or validator could do -- deterministic checks are cheaper and more reliable than LLM reasoning. Reserve prose instructions for decisions that genuinely require judgment.

## Workflows with Feedback Loops

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

## Evaluation-Driven Development

Start with a minimal SKILL.md addressing only observed gaps. Add content only when testing reveals the agent needs it -- not preemptively.

Build evaluations BEFORE writing extensive documentation:

1. **Identify gaps**: Run the agent on representative tasks without the skill. Note specific failures
2. **Create evaluations**: Define three test scenarios covering those gaps
3. **Establish baseline**: Measure performance without the skill
4. **Write minimal instructions**: Just enough to address gaps and pass evaluations
5. **Iterate**: Execute evaluations, compare against baseline, refine

## Iterative Author-Tester Workflow

1. **Instance A** (author): Helps create/refine skill content
2. **Instance B** (tester): Uses the skill on real tasks in a fresh session
3. Observe Instance B's behavior -- where it struggles, succeeds, or makes unexpected choices. Grade outcomes, not paths: agents may find valid approaches you didn't anticipate
4. Bring observations back to Instance A for refinements
5. Repeat until the skill reliably handles target scenarios

## Observe Navigation Patterns

Watch how the agent uses the skill:

- Unexpected file access order -> structure isn't intuitive
- Missed references -> links need to be more explicit
- Overreliance on one file -> content should be in `SKILL.md`
- Ignored files -> unnecessary or poorly signaled

## Executable Code Best Practices

**Solve, Don't Punt**: Handle error conditions explicitly rather than letting scripts fail for the agent to debug.

**Justify Constants**: Document why values exist -- no voodoo numbers:

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
