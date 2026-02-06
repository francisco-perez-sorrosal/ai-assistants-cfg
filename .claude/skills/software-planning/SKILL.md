---
name: software-planning
description: Planning complex software tasks using a three-document model for tracking work in small, known-good increments. Use when starting significant software work or breaking down complex development tasks.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, TaskCreate, TaskUpdate, TaskList]
---

# Software Planning in Small Increments

**All work must be done in small, known-good increments.** Each increment leaves the codebase in a working state.
Create and maintain planning documents (PLAN.md, WIP.md, LEARNINGS.md) directly using Write and Edit tools.

## Three-Document Model

For significant work, maintain three documents:

| Document | Purpose | Lifecycle |
|----------|---------|-----------|
| **PLAN.md** | What we're doing | Created at start, changes need approval |
| **WIP.md** | Where we are now | Updated constantly, always accurate |
| **LEARNINGS.md** | What we discovered | Temporary, merged at end then deleted |

### Document Relationships

```
PLAN.md (static)          WIP.md (living)           LEARNINGS.md (temporary)
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ Goal            │       │ Current step    │       │ Gotchas         │
│ Acceptance      │  ──►  │ Status          │  ──►  │ Patterns        │
│ Steps 1-N       │       │ Blockers        │       │ Decisions       │
│ (approved)      │       │ Next action     │       │ Edge cases      │
└─────────────────┘       └─────────────────┘       └─────────────────┘

END OF FEATURE: Merge LEARNINGS into CLAUDE.md / ADRs, then DELETE all three docs
```

## Language Context

When planning work in a specific language or tech stack, load the relevant **context overlay** alongside this skill. Contexts augment the planning workflow with language-specific quality gates, step templates, and testing patterns — without duplicating content from language skills.

**Available contexts**:

| Context | File | Related Skills |
|---------|------|----------------|
| Python | [contexts/python.md](contexts/python.md) | [Python](../python/SKILL.md), [Python Project Management](../python-prj-mgmt/SKILL.md) |

**How contexts integrate**:
- **PLAN.md**: Add a `Tech Stack` field linking to the relevant context and skills
- **Step templates**: Use language-specific templates for common step types (new module, add dependency, etc.)
- **Quality gates**: Run language-specific checks (linter, type checker, tests) before each commit
- **Testing field**: Choose testing approach based on language-specific patterns

If no context exists for your language, use the generic planning workflow and reference language-specific documentation directly.

## Phase Delegations

Some plan steps delegate to a **specialized skill** for their methodology. A phase is a group of consecutive steps that follow a specialized skill's workflow while remaining tracked by the plan.

**Available phases**:

| Phase | File | Delegated Skill |
|-------|------|-----------------|
| Refactoring | [phases/refactoring.md](phases/refactoring.md) | [Refactoring](../refactoring/SKILL.md) |

**How phases integrate**:
- **Detection**: During plan creation, look for signals that a phase is needed (each phase doc lists its signals)
- **Step marking**: Tag delegated steps with `[Phase: <Name>]` in the step title and a `Skill` field pointing to the delegated skill
- **Entry/exit criteria**: Each phase defines what must be true before starting and after completing
- **Scoped**: Phase steps serve the plan's goal — they are not open-ended improvement

**Delegated step template**:

```markdown
### Step N: [Phase: <Name>] One sentence description

**Skill**: [<Skill Name>](link/to/SKILL.md)
**Implementation**: What structural change will we make?
**Testing**: How do we verify behavior is preserved / new behavior works?
**Done when**: Concrete exit condition
```

**Contexts and phases compose**: A plan can use a language context (Python quality gates) *and* a phase (refactoring methodology) simultaneously. The context provides the quality checks; the phase provides the approach.

## What Makes a "Known-Good Increment"

Each step MUST:

- Leave the system in a working state
- Be independently testable
- Have clear done criteria
- Fit in a single commit
- Be describable in one sentence

**If you can't describe a step in one sentence, break it down further.**

## Step Size Heuristics

**Too big if:**

- Takes more than one session
- Requires multiple commits to complete
- Has multiple "and"s in description
- Involves more than 3-5 files
- Tests would be too complex to write

**Right size if:**

- One clear objective
- One logical change
- Can explain to someone in 30 seconds
- Obvious when done
- Single responsibility

## Testing Strategy

**Pragmatic testing**: Test critical paths, complex logic, and integrations.

**Write tests for:**

- Complex algorithms or business logic
- Critical user flows
- Integration points between components
- Edge cases in important features
- Anything that's been a source of bugs

**Don't test:**

- Simple getters/setters
- Obvious code with no logic
- Framework-provided functionality
- Code that will be deleted soon

**When to write tests:**

- Before implementation for critical/complex components
- After implementation for straightforward features
- When instructed or requested
- When fixing bugs (regression tests)

## Commit Discipline

**NEVER commit without user approval.**

After completing a step:

1. Verify system is in working state
2. Run relevant tests if they exist
3. Verify static analysis passes
4. Update WIP.md with progress
5. Capture any learnings in LEARNINGS.md
6. **STOP and ask**: "Ready to commit [description]. Approve?"

Only proceed with commit after explicit approval.

## PLAN.md Structure

```markdown
# Plan: [Feature Name]

## Goal

[One sentence describing the outcome]

## Tech Stack

[Language/framework and relevant context, e.g., "Python 3.13 with pixi — see [Python context](contexts/python.md)"]

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Steps

### Step 1: [One sentence description]

**Implementation**: What code will we write?
**Testing**: What needs testing? (if critical/complex)
**Done when**: How do we know it's complete?

### Step N: [One sentence description]

**Implementation**: ...
**Testing**: ...
**Done when**: ...
```

### Plan Changes Require Approval

If the plan needs to change:

1. Explain what changed and why
2. Propose updated steps
3. **Wait for approval** before proceeding

Plans are not immutable, but changes must be explicit and approved.

## WIP.md Structure

```markdown
# WIP: [Feature Name]

## Current Step

Step N of M: [Description]

## Status

[IMPLEMENTING] - Writing code
[TESTING] - Writing/running tests
[REVIEWING] - Checking quality
[WAITING] - Awaiting commit approval
[COMPLETE] - Step finished

## Progress

- [x] Step 1: [Description]
- [x] Step 2: [Description]
- [ ] Step 3: [Description] ← current
- [ ] Step 4: [Description]

## Blockers

[None / List current blockers]

## Next Action

[Specific next thing to do]

## Notes

[Optional: Brief notes about current work]
```

### WIP Must Always Be Accurate

Update WIP.md:

- When starting a new step
- When status changes
- When blockers appear or resolve
- After each commit
- At end of each session

**If WIP.md doesn't reflect reality, update it immediately.**

## LEARNINGS.md Structure

```markdown
# Learnings: [Feature Name]

## Gotchas
- **[Title]**: Context, issue, solution

## Patterns That Worked
- **[Title]**: What, why it works, brief example

## Decisions Made
- **[Title]**: Options considered, decision, rationale, trade-offs

## Edge Cases
- [Edge case]: How we handled it

## Technical Debt
- [Item]: What was compromised, why, future improvement needed
```

### Capture Learnings As They Occur

Don't wait until the end. When you discover something:

1. Add it to LEARNINGS.md immediately
2. Continue with current work
3. At end of feature, learnings are ready to merge

## Workflow Example

```
START: Create PLAN.md (get approval) + WIP.md + LEARNINGS.md

FOR EACH STEP:
  1. Update WIP.md (IMPLEMENTING)
  2. Write implementation + tests (if critical)
  3. Verify system works, run quality checks
  4. Capture learnings, update WIP.md (WAITING)
  5. WAIT FOR COMMIT APPROVAL

END: Verify all criteria met, merge learnings, delete all three docs
```

## End of Feature

When all steps are complete:

### 1. Verify Completion

- All acceptance criteria met
- System is working
- Critical components tested
- All steps marked complete in WIP.md

### 2. Merge Learnings

Review LEARNINGS.md and determine destination:

| Learning Type | Destination | Notes |
|---------------|-------------|-------|
| Gotchas | CLAUDE.md | Add to relevant section |
| Patterns | CLAUDE.md | Document successful approaches |
| Architectural decisions | ADR or CLAUDE.md | Significant decisions get ADRs |
| Technical debt | Issue tracker or CLAUDE.md | Track future improvements |
| Domain knowledge | Project docs | Update relevant documentation |

### 3. Delete Documents

After learnings are merged:

```bash
rm PLAN.md WIP.md LEARNINGS.md
git add PLAN.md WIP.md LEARNINGS.md
git commit -m "chore: complete [feature], remove planning docs"
```

**The knowledge lives on in:**

- CLAUDE.md (gotchas, patterns, decisions)
- Git history (what was done)
- Project documentation (if applicable)
- Issue tracker (technical debt)

## Breaking Down Complex Features

### Start with the Goal

**Bad**: "Improve user authentication"
**Good**: "Add OAuth2 login alongside existing email/password authentication"

### Identify Acceptance Criteria

What does "done" look like?

- [ ] Users can log in with Google OAuth2
- [ ] Existing email/password login still works
- [ ] User accounts are linked correctly
- [ ] Error states are handled gracefully

### Decompose into Steps

Ask: "What's the smallest change that moves toward the goal?"

Before listing feature steps, check for **phase signals** — does the current codebase need preparatory work (refactoring, migration, etc.) before the feature can be built cleanly? If yes, prepend a [phase delegation](#phase-delegations) to the step list.

**Example breakdown:**

1. Add OAuth2 library dependency
2. Create OAuth2 configuration module
3. Implement OAuth2 callback handler
4. Add user account linking logic
5. Update login UI to show OAuth2 option
6. Add error handling for OAuth2 failures
7. Test integration with Google OAuth2

Each step is one commit, leaves system working.

### Validate Step Size

For each step, ask:

- Can I describe this in one sentence? (yes)
- Can I do this in one session? (yes)
- Will the system still work after? (yes)
- Is it obvious when I'm done? (yes)

If any answer is "no", break it down further.

## Handling Unknowns

### Spike Steps

For exploratory work, add spike steps:

```markdown
### Step 2: Spike - Investigate OAuth2 library options

**Implementation**: Research and test 2-3 OAuth2 libraries
**Done when**: Decision made and documented in LEARNINGS.md
**Timebox**: 1 hour max
```

**Spike characteristics:**

- Timeboxed exploration
- May not result in production code
- Must produce a decision
- Document findings in LEARNINGS.md

After a spike, update the plan: document findings in LEARNINGS.md, propose plan changes, get approval, then continue.

## Anti-Patterns

**Don't:** Commit without approval — always wait for explicit "yes" before committing

**Don't:** Let steps span multiple commits — break down further until one step = one commit

**Don't:** Use vague "done when" criteria — "when it works" is not specific enough. Be concrete: "When users can log in with Google and existing tests pass"

**Don't:** Let WIP.md become stale — update immediately when reality changes

**Don't:** Wait until end to capture learnings — add to LEARNINGS.md as discoveries occur

**Don't:** Change plans silently — all plan changes require discussion and approval

**Don't:** Keep planning docs after feature complete — delete them; knowledge is now in permanent locations

**Don't:** Skip tests for complex logic — critical and complex components need tests; don't defer testing indefinitely

## When to Use This Skill

**Use three-document planning for:**

- Features taking multiple sessions
- Complex features with many moving parts
- Work with architectural implications
- Projects where requirements may evolve
- Collaborative work needing clear status
- Anything where you need to track progress over time

**Skip for simple tasks:**

- Bug fixes (unless complex)
- Simple feature additions (1-2 files)
- Refactoring within single module
- Documentation updates
- Configuration changes

**Use TaskCreate/TaskUpdate for simple multi-step tasks instead.**

## Integration with Task Tools

**PLAN.md vs Task Tools (TaskCreate/TaskUpdate/TaskList):**

| Use PLAN.md when: | Use Task Tools when: |
|-------------------|----------------------|
| Multi-session feature | Single-session task |
| Need to capture learnings | Simple checklist |
| Complex dependencies | Independent tasks |
| Requirements may evolve | Clear requirements |
| Need approval for plan changes | Straightforward execution |

**Can use both**: Task tools track current session's micro-tasks, PLAN.md tracks overall feature steps.

## Quick Reference

### Document Purposes

- **PLAN.md**: The contract - what we agreed to build
- **WIP.md**: The dashboard - where we are right now
- **LEARNINGS.md**: The notebook - what we're discovering

### Update Triggers

| Trigger | Update |
|---------|--------|
| Start new step | WIP.md status and progress |
| Discover gotcha | LEARNINGS.md gotchas section |
| Make decision | LEARNINGS.md decisions section |
| Complete step | WIP.md progress checklist |
| Hit blocker | WIP.md blockers section |
| Plan changes | PLAN.md + get approval |
| End of session | WIP.md next action |

### Checklist Before Commit Approval

- [ ] System is in working state
- [ ] Relevant tests pass (if tests exist)
- [ ] Static analysis passes
- [ ] Language-specific quality gates pass (see [Language Context](#language-context))
- [ ] WIP.md reflects current state
- [ ] Learnings captured if any
- [ ] Can describe change in one sentence

## Summary

Planning with the three-document model:

1. **Start**: Create PLAN.md (approved), WIP.md, LEARNINGS.md
2. **Execute**: One step at a time, one commit per step
3. **Track**: Keep WIP.md accurate, capture learnings immediately
4. **Finish**: Merge learnings, delete all three documents

**The goal**: Break complex work into simple steps, maintain working state, capture knowledge, and always know where you are.
