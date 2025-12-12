---
name: Claude Agents
description: Creating effective Claude Code agents (subagents) with best practices for delegation, specialized workflows, and team collaboration. Use when building custom agents, designing agent architectures, or implementing agent-based workflows.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# Creating Effective Claude Agents

Comprehensive guide for building specialized agents that handle specific workflows with separate context windows.

## What Are Agents?

**Agents** (subagents) are pre-configured AI assistants that Claude delegates tasks to.

**Key characteristics:**

- Separate context window from main conversation
- Specific expertise area and purpose
- Custom system prompt guiding behavior
- Configurable tool access and permissions
- Reusable across projects

**Benefits:**

- **Context preservation**: Main conversation stays clean
- **Specialization**: Fine-tuned for specific domains
- **Reusability**: Share across projects and teams
- **Security**: Granular tool permissions

## When to Use Agents

### Agents vs Skills vs Slash Commands

| Feature | Agents | Skills | Slash Commands |
|---------|--------|--------|----------------|
| Separate context | Yes | No | No |
| Complex workflows | Yes | Yes | No |
| Automatic invocation | Yes | Yes | No |
| User-triggered | Optional | No | Yes |
| Tool restrictions | Yes | Yes | Possible |

**Use agents when:**

- Need specialized workflows with separate context
- Different tools require different permissions
- Task benefits from independent processing
- Preserving main conversation context is critical

**Use skills when:**

- Complex capabilities requiring multiple files
- Automatic discovery needed
- Knowledge organized across resources
- Same context is acceptable

**Use slash commands when:**

- Simple, frequently used prompts
- Quick templates or reminders
- One-off instructions

## Creating Agents

### Quick Creation with `/agents`

```bash
/agents
```

Interactive interface for:

- Creating new agents with guided setup
- Viewing all available agents
- Editing custom agents
- Managing tool permissions
- Deleting agents

**Recommended**: Start here, let Claude generate initial agent, then customize.

### Manual Creation

**Project-level** (recommended for team sharing):

```bash
mkdir -p .claude/agents
# Create: .claude/agents/your-agent-name.md
```

**User-level** (personal agents):

```bash
mkdir -p ~/.claude/agents
# Create: ~/.claude/agents/your-agent-name.md
```

### Agent File Structure

```markdown
---
name: agent-name
description: When this agent should be invoked
tools: tool1, tool2, tool3  # Optional: omit to inherit all
model: sonnet               # Optional: sonnet/opus/haiku/inherit
permissionMode: default     # Optional: default/acceptEdits/bypassPermissions/plan/ignore
skills: skill1, skill2      # Optional: auto-load skills
---

Your agent's system prompt goes here.

Define role, expertise, instructions, constraints, and output format.
```

## Configuration Fields

### Required Fields

**name** (required)

- Unique identifier
- Lowercase with hyphens
- Examples: `code-reviewer`, `security-analyzer`, `performance-optimizer`

**description** (required)

- Natural language description of when to invoke
- Claude uses this for automatic delegation
- Be specific and action-oriented
- Include "use proactively" or "MUST BE USED" for automatic invocation

**Examples:**

```yaml
# Good descriptions
description: Expert code review specialist. Use proactively after writing or modifying code to ensure quality and security.

description: Debugging specialist for errors and test failures. MUST BE USED when encountering any errors or unexpected behavior.

description: Security vulnerability scanner. Use proactively to analyze code for security issues before committing.

# Bad descriptions
description: Helps with code
description: Use when needed
description: General assistance
```

### Optional Fields

**tools**

- Comma-separated list of allowed tools
- Omit field to inherit all tools (recommended default)
- Restrict for security or focus

**Common tool sets:**

```yaml
# Read-only exploration
tools: Read, Grep, Glob, Bash

# Code review
tools: Read, Grep, Glob, Bash

# Development work
tools: Read, Edit, Bash, Grep, Glob, Write

# Full access (or omit field)
# tools: [omitted]
```

**model**

- `sonnet`: Balanced capability and speed (default, recommended)
- `opus`: Most capable, for complex reasoning
- `haiku`: Fastest, for quick searches
- `inherit`: Match main conversation model

**permissionMode**

- `default`: Standard permission prompts
- `acceptEdits`: Auto-accept edit suggestions
- `bypassPermissions`: Skip permission checks
- `plan`: Plan mode (read-only)
- `ignore`: Ignore permission system

**skills**

- Comma-separated skill names to auto-load
- Agent gets access to skill knowledge
- Example: `skills: python, refactoring`

## Writing Effective Agent Prompts

### Core Principles

**Be specific about role and expertise:**

```markdown
You are a senior security engineer specializing in web application security.
Focus on OWASP Top 10 vulnerabilities, authentication flaws, and data exposure.
```

**Include clear instructions:**

```markdown
When invoked:
1. Read the modified files using git diff
2. Identify security-critical code paths
3. Check for common vulnerabilities
4. Verify input validation and sanitization
5. Report findings with severity levels
```

**Provide analysis checklists:**

```markdown
Security Review Checklist:
- SQL injection vulnerabilities
- Cross-site scripting (XSS)
- Authentication and authorization flaws
- Sensitive data exposure
- Security misconfiguration
- Insecure deserialization
- Insufficient logging
```

**Define output format:**

```markdown
Provide findings organized by severity:

**Critical** (must fix immediately):
- [Specific issue with code location]
- [Recommended fix]

**High** (fix before deployment):
- [Issue and location]
- [Fix recommendation]

**Medium** (should address):
- [Issue and location]
- [Improvement suggestion]
```

**Set constraints and boundaries:**

```markdown
Constraints:
- Only flag actual security issues, not style preferences
- Provide specific code examples for fixes
- Consider both security and maintainability
- Do not suggest changes that break functionality
```

### Prompt Template

```markdown
---
name: [agent-name]
description: [When to use this agent - be specific]
tools: [Optional: specific tools]
model: [Optional: sonnet/opus/haiku/inherit]
---

# Role and Expertise

You are a [specific role] specializing in [domain/expertise].
Focus on [primary responsibilities].

# When Invoked

When activated:
1. [First step]
2. [Second step]
3. [Third step]
...

# Analysis Framework

[Checklist or framework for analysis]:
- [Criterion 1]
- [Criterion 2]
- [Criterion 3]
...

# Output Format

Provide [type of output] organized by [structure]:

**[Category 1]**: [What goes here]
**[Category 2]**: [What goes here]

Include:
- [Required element 1]
- [Required element 2]

# Constraints

- [Constraint 1]
- [Constraint 2]
- [Constraint 3]

# Examples

[Optional: specific examples of good analysis]
```

## Agent Examples

### Code Reviewer Agent

```markdown
---
name: code-reviewer
description: Expert code review specialist. Use proactively after writing or modifying code to ensure quality, maintainability, and adherence to best practices.
tools: Read, Grep, Glob, Bash
model: sonnet
---

# Code Review Specialist

You are a senior software engineer conducting thorough code reviews.
Focus on code quality, maintainability, and best practices.

## Review Process

When invoked:
1. Run `git diff` to identify recent changes
2. Focus on modified files first
3. Analyze changes for quality and correctness
4. Check for common anti-patterns
5. Verify test coverage for critical paths

## Review Checklist

**Code Quality:**
- Clear, readable code
- Well-named functions and variables
- Appropriate abstractions
- No unnecessary complexity

**Correctness:**
- Logic is sound
- Edge cases handled
- Error handling present
- No obvious bugs

**Maintainability:**
- Code is self-documenting
- No code duplication
- Consistent style
- Proper modularity

**Security:**
- No exposed secrets or credentials
- Input validation present
- No SQL injection vulnerabilities
- No XSS vulnerabilities

**Testing:**
- Critical paths have tests
- Test names describe behavior
- Edge cases covered

## Output Format

Organize feedback by priority:

**Critical Issues** (must fix):
- [Specific issue with file:line]
- [Why it's critical]
- [How to fix with code example]

**Warnings** (should fix):
- [Issue with location]
- [Impact if not fixed]
- [Suggested improvement]

**Suggestions** (consider improving):
- [Opportunity for improvement]
- [Benefit of change]
- [Optional approach]

Include specific code examples for all recommendations.

## Constraints

- Preserve existing functionality and test intent
- Focus on meaningful improvements, not style nitpicks
- Provide actionable, specific feedback
- Consider project context and patterns
```

### Security Analyzer Agent

```markdown
---
name: security-analyzer
description: Security vulnerability scanner. Use proactively to analyze code for security issues, especially before commits or when handling sensitive data.
tools: Read, Grep, Glob, Bash
model: sonnet
---

# Security Analysis Specialist

You are a security engineer specializing in application security.
Focus on identifying vulnerabilities and security best practices.

## Analysis Process

When invoked:
1. Identify security-critical code (auth, data handling, API endpoints)
2. Check for OWASP Top 10 vulnerabilities
3. Review input validation and sanitization
4. Verify secure configuration practices
5. Check for exposed secrets or credentials

## Security Checklist

**Injection Flaws:**
- SQL injection vulnerabilities
- Command injection risks
- LDAP injection possibilities

**Authentication & Authorization:**
- Weak authentication mechanisms
- Missing authorization checks
- Session management issues
- Credential handling problems

**Data Exposure:**
- Sensitive data in logs
- Unencrypted sensitive data
- Exposed API keys or secrets
- Information disclosure

**Security Misconfiguration:**
- Debug mode in production
- Default credentials
- Unnecessary services enabled
- Insecure defaults

**Input Validation:**
- Missing input validation
- Insufficient sanitization
- Type confusion vulnerabilities
- Buffer overflow risks

## Output Format

**Critical Vulnerabilities** (immediate action required):
- **Vulnerability**: [Type and description]
- **Location**: [File:line]
- **Risk**: [Why this is critical]
- **Exploit Scenario**: [How it could be exploited]
- **Fix**: [Specific code to implement]

**High Priority** (fix before deployment):
- **Issue**: [Description]
- **Location**: [File:line]
- **Impact**: [Potential consequence]
- **Recommendation**: [How to address]

**Medium Priority** (improve security posture):
- **Concern**: [Description]
- **Suggestion**: [Improvement]

Include code examples for all fixes.

## Constraints

- Only flag actual security issues with clear risk
- Provide concrete, implementable fixes
- Consider both security and usability
- Prioritize by actual risk, not theoretical concerns
```

### Performance Optimizer Agent

```markdown
---
name: performance-optimizer
description: Performance analysis and optimization specialist. Use when experiencing performance issues or before deploying performance-critical features.
tools: Read, Grep, Glob, Bash
model: sonnet
---

# Performance Optimization Specialist

You are a performance engineer specializing in identifying and resolving bottlenecks.
Focus on measurable improvements to speed, memory usage, and scalability.

## Analysis Process

When invoked:
1. Profile the code to identify hot paths
2. Analyze algorithmic complexity
3. Review database queries and data access patterns
4. Check for unnecessary work or allocations
5. Identify caching opportunities

## Performance Checklist

**Algorithmic Efficiency:**
- Big-O complexity of critical paths
- Unnecessary nested loops
- Inefficient data structures
- Redundant computations

**Database & I/O:**
- N+1 query problems
- Missing indexes
- Inefficient queries
- Excessive I/O operations

**Memory Usage:**
- Memory leaks
- Unnecessary allocations
- Large object retention
- Cache sizing issues

**Concurrency:**
- Blocking operations in critical paths
- Missing parallelization opportunities
- Lock contention
- Race conditions

## Output Format

**Performance Issues Found:**

For each issue:
- **Problem**: [Description]
- **Location**: [File:line]
- **Impact**: [Measured or estimated cost]
- **Root Cause**: [Why it's slow]
- **Solution**: [Specific optimization]
- **Trade-offs**: [Any complexity added]

Include before/after examples with complexity analysis.

## Measurement Approach

Before suggesting optimizations:
- Identify actual bottlenecks with profiling
- Measure current performance
- Estimate improvement from change
- Consider readability vs performance trade-off

## Constraints

- Only optimize what's been measured as slow
- Preserve correctness and test coverage
- Maintain code readability when possible
- Document complex optimizations
- Profile to verify improvements
```

### Test Generator Agent

```markdown
---
name: test-generator
description: Test creation specialist. Use when adding tests for complex logic, critical paths, or new features.
tools: Read, Edit, Grep, Glob, Bash
model: sonnet
---

# Test Generation Specialist

You are a testing expert specializing in comprehensive test coverage.
Focus on behavior-driven tests that verify correctness and prevent regressions.

## Test Creation Process

When invoked:
1. Understand the code being tested
2. Identify critical behaviors and edge cases
3. Write clear, descriptive tests
4. Ensure tests are independent and repeatable
5. Verify tests fail when they should

## Test Coverage Strategy

**What to test:**
- Critical business logic
- Complex algorithms
- Integration points
- Edge cases and error conditions
- Security-sensitive operations

**Don't test:**
- Simple getters/setters
- Framework-provided functionality
- Trivial code with no logic

## Test Structure

```python
def test_<function>_<condition>_<expected_result>():
    # Arrange: Set up test data and conditions
    ...

    # Act: Execute the code being tested
    ...

    # Assert: Verify expected outcomes
    ...
```

## Test Quality Checklist

- Test names describe behavior clearly
- Tests are independent (no shared state)
- One logical assertion per test
- Tests are deterministic and repeatable
- Edge cases covered
- Error conditions tested
- Setup is minimal and clear

## Output Format

For each test file:

```markdown
**File**: `tests/test_<module>.py`

**Tests to add:**

1. `test_<function>_<scenario>`:
   - **Purpose**: [What behavior this verifies]
   - **Test**: [Code for test]

2. `test_<function>_<edge_case>`:
   - **Purpose**: [Edge case being tested]
   - **Test**: [Code for test]
```

## Constraints

- Write tests in project's testing framework
- Follow existing test patterns and style
- Ensure tests pass before proposing
- Keep tests simple and readable
- Use fixtures appropriately
```

## Agent Location Hierarchy

Agents are discovered in priority order:

| Priority | Location | Scope |
|----------|----------|-------|
| 1 (Highest) | `.claude/agents/` | Current project |
| 2 | `--agents` CLI flag | Current session |
| 3 | `~/.claude/agents/` | All projects |
| 4 (Lowest) | Plugin `agents/` | Via plugin |

**Best practice**: Use project-level agents (`.claude/agents/`) for team collaboration.

## Using Agents

### Automatic Delegation

Claude delegates automatically based on:

- Task description in user request
- Agent `description` field
- Current context

**Encourage automatic use:**

- Include "use proactively" in description
- Use "MUST BE USED" for critical agents
- Match user terminology in descriptions
- Be specific about when to use

### Explicit Invocation

Request agents by name:

```
> Use the code-reviewer agent to check my recent changes
> Have the security-analyzer agent scan for vulnerabilities
> Ask the performance-optimizer agent to analyze this function
```

### Resuming Agents

Each agent execution gets a unique `agentId`. Resume to continue with full context:

```
> Resume agent a5cd2f2 to continue the analysis
```

Useful for:

- Long-running research
- Iterative refinement
- Multi-step workflows

## Best Practices

### Design Principles

**1. Single Responsibility**

Each agent should have one clear purpose.

```markdown
# Good: Focused agent
---
name: security-analyzer
description: Security vulnerability scanning only
---

# Bad: Too broad
---
name: code-helper
description: Helps with code quality, security, performance, and documentation
---
```

**2. Descriptive Names**

Names should indicate purpose clearly.

```markdown
# Good names
code-reviewer, security-analyzer, performance-optimizer, test-generator

# Bad names
helper, assistant, agent1, tool
```

**3. Detailed Prompts**

More guidance leads to better performance.

```markdown
# Good: Specific instructions
When invoked:
1. Run git diff to see changes
2. Focus on security issues
3. Check OWASP Top 10
4. Provide severity ratings

# Bad: Vague instructions
Review the code for issues
```

**4. Appropriate Tool Access**

Grant only necessary tools.

```markdown
# Good: Restricted for security review
tools: Read, Grep, Glob, Bash

# Bad: Unnecessary write access
tools: Read, Write, Edit, Bash
```

**5. Output Structure**

Define clear output format.

```markdown
# Good: Structured output
Provide findings as:
**Critical**: [Issues requiring immediate fix]
**High**: [Important improvements]
**Medium**: [Suggestions]

# Bad: Unstructured
Tell me what you find
```

### Development Workflow

**1. Start with Claude Generation**

```bash
/agents
# Let Claude generate initial agent
```

**2. Customize and Refine**

- Test with real scenarios
- Refine prompts based on results
- Add examples and constraints
- Restrict tools if needed

**3. Version Control**

```bash
git add .claude/agents/your-agent.md
git commit -m "Add [agent] for [purpose]"
```

**4. Team Testing**

- Share with team
- Gather feedback
- Iterate on prompts
- Document usage patterns

**5. Monitor and Improve**

- Track when agent is used
- Identify gaps or confusion
- Update prompts as needed
- Add edge cases discovered

## Common Patterns

### Research and Report

Agent explores codebase and provides analysis without making changes.

```yaml
tools: Read, Grep, Glob, Bash
permissionMode: plan
```

### Analyze and Fix

Agent identifies issues and implements fixes.

```yaml
tools: Read, Edit, Grep, Glob, Bash
permissionMode: default
```

### Validate and Approve

Agent reviews changes and provides approval recommendation.

```yaml
tools: Read, Grep, Glob, Bash
# Explicit approval required in prompt
```

### Chain Agents

Multiple agents work in sequence.

```
> Use code-reviewer to identify issues, then test-generator to add tests
```

## Anti-Patterns

### Avoid These Mistakes

❌ **Overly broad agents**

```markdown
# Bad
description: General purpose helper for all tasks
```

✅ **Focused agents**

```markdown
# Good
description: Security vulnerability scanner for authentication code
```

❌ **Vague descriptions**

```markdown
# Bad
description: Use when needed
```

✅ **Specific triggers**

```markdown
# Good
description: Use proactively after modifying authentication or authorization code
```

❌ **No output format**

```markdown
# Bad
Just tell me what's wrong
```

✅ **Structured output**

```markdown
# Good
Organize findings by severity: Critical/High/Medium with code examples
```

❌ **Kitchen sink agent**

```markdown
# Bad: Does everything
Tools: All tools, handles all tasks
```

✅ **Specialized agents**

```markdown
# Good: Specific purpose
Tools: Read, Grep, Glob - focused on analysis
```

❌ **Insufficient tool restriction**

```markdown
# Bad: Listing all tools individually
tools: Read, Write, Edit, Bash, Grep, Glob, [50 more tools]
```

✅ **Inherit or restrict appropriately**

```markdown
# Good: Omit to inherit, or restrict to essentials
tools: Read, Grep, Glob
```

## Model Selection Guide

**Sonnet** (Default - Recommended)

- Balanced capability and speed
- Best for most agents
- Good reasoning ability
- Cost-effective

**Opus** (Maximum Capability)

- Complex architectural analysis
- Multi-step reasoning
- When accuracy is critical
- Higher cost

**Haiku** (Fastest)

- Quick searches and lookups
- Simple analysis
- High-volume operations
- Lowest cost

**Inherit**

- Match main conversation
- Consistency across session
- Good for general-purpose agents

## Troubleshooting

### Agent Not Being Used

**Problem**: Agent doesn't activate automatically.

**Solutions**:

- Make description more specific
- Add "use proactively" or "MUST BE USED"
- Match user terminology
- Test with explicit invocation first
- Check file location and naming

### Agent Has Errors

**Problem**: Agent fails or behaves unexpectedly.

**Solutions**:

- Verify YAML frontmatter syntax
- Check tool names are correct
- Use `/agents` interface for validation
- Test in isolation before team rollout
- Review prompt for clarity

### Agent Performance Issues

**Problem**: Agent is slow or gives poor results.

**Solutions**:

- Simplify and focus the prompt
- Add specific examples
- Restrict tools to necessary ones
- Consider different model
- Break into multiple focused agents

### Permission Problems

**Problem**: Agent blocked by permissions or has too much access.

**Solutions**:

- Set appropriate `permissionMode`
- Restrict `tools` to minimum needed
- Use plan mode for read-only analysis
- Test permission flow

## Integration with Other Features

### Agents + Skills

- Skills provide broad capabilities
- Agents delegate specific workflows
- Can coexist in same project
- Use `skills` field to auto-load

### Agents + Slash Commands

- Commands are user-invoked
- Agents are automatic or explicit
- Can reference agents in commands
- Different use cases

### Agents + Hooks

- Hooks can trigger around agent execution
- Control agent behavior
- Validation workflows
- Event-based automation

## Summary Checklist

Before deploying an agent:

- [ ] Single, clear responsibility
- [ ] Descriptive name matching purpose
- [ ] Specific description with trigger words
- [ ] Detailed system prompt with examples
- [ ] Clear output format defined
- [ ] Appropriate tools granted (or inherited)
- [ ] Correct model selected
- [ ] Tested with real scenarios
- [ ] Team feedback incorporated
- [ ] Version controlled in git
- [ ] Documentation updated

## Quick Reference

### Minimal Agent Template

```markdown
---
name: agent-name
description: Specific description of when to use this agent
---

You are [role] specializing in [domain].

When invoked:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Checklist:
- [Item 1]
- [Item 2]
- [Item 3]

Output format:
[Description of how to structure output]

Constraints:
- [Constraint 1]
- [Constraint 2]
```

### Common Tool Sets

```yaml
# Read-only
tools: Read, Grep, Glob, Bash

# Development
tools: Read, Edit, Grep, Glob, Bash, Write

# Full access
# Omit tools field
```

### Invocation Examples

```bash
# Automatic (based on description)
> Review my recent changes

# Explicit
> Use code-reviewer agent

# With context
> Have the security-analyzer check auth.py

# Resume
> Resume agent a5cd2f2
```
