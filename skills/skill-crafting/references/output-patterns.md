# Output Patterns

Patterns for skills that need to produce consistent, high-quality output. Reference material for the [Skill Creator](../SKILL.md) skill.

## Template Pattern

Use templates when the skill's output must follow a specific structure. Match template strictness to requirements.

### Strict Template

When the output format is non-negotiable (reports, compliance documents, structured data):

```markdown
Use this EXACT template for every security audit report:

# Security Audit Report

## Executive Summary
[2-3 sentence overview of findings]

## Key Findings
- Finding 1: [description] | Severity: [Critical/High/Medium/Low]
- Finding 2: [description] | Severity: [Critical/High/Medium/Low]

## Recommendations
1. [Immediate action items]
2. [Short-term improvements]
3. [Long-term architectural changes]

## Methodology
[Brief description of audit approach]
```

### Flexible Template

When a sensible default exists but adaptation is expected:

```markdown
Use this format as a sensible default, adapting sections as needed
for the specific context:

# [Component] Design Document

## Problem Statement
## Proposed Solution
## Alternatives Considered
## Implementation Plan
```

## Examples Pattern

Use input/output pairs when the desired style and detail level are easier to show than describe. Examples help the agent understand conventions more clearly than prose descriptions alone.

### Showing Desired Style

Provide concrete before/after pairs that demonstrate the target quality:

```markdown
Format commit messages following this pattern:

type(scope): brief description

Examples:
- feat(auth): add OAuth2 token refresh flow
- fix(parser): handle empty input without panic
- refactor(db): extract connection pooling to module
- docs(api): document rate limiting headers
```

### Showing Detail Level

When the expected depth of output matters, include examples at the target level:

```markdown
When documenting a function, match this level of detail:

Input: `def retry(fn, max_attempts=3, backoff=1.0)`

Output:
Retry a callable with exponential backoff.
- `fn`: Zero-argument callable to retry
- `max_attempts`: Maximum number of attempts before raising (default: 3)
- `backoff`: Initial delay in seconds, doubled after each failure (default: 1.0)
- Raises the last exception if all attempts fail
```
