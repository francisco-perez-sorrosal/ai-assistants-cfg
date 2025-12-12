# Claude Agents

Custom agents for specialized workflows. Agents are autonomous subprocesses that Claude spawns to handle complex, multi-step tasks.

## Available Agents

### plan-executor

**Purpose**: Manages significant work through small, known-good increments using three tracking documents.

**Three-Document System**:

| Document | Purpose | Updates |
|----------|---------|---------|
| `PLAN.md` | Approved steps | Only with user approval |
| `WIP.md` | Current state | Constantly |
| `LEARNINGS.md` | Discoveries | As they occur |

**Use for**:
- Multi-session features
- Complex work with many moving parts
- Work with architectural implications
- Projects where requirements may evolve

**Skip for**:
- Simple bug fixes
- Single-file changes
- Documentation/config updates
- Use `TodoWrite` for simple multi-step tasks instead

**Key behaviors**:
- Small increments (one commit per step, system always working)
- Pragmatic testing (test critical/complex code only)
- Plan/commit changes require approval
- Captures learnings as they occur
- At end: merges learnings to permanent locations, deletes all three docs

**Related**: See `planning` skill for detailed principles.

---

For creating custom agents, see the `claude-agents` skill documentation.
