---
name: Planning
description: Planning complex software tasks using a three-document model for tracking work in small, known-good increments. Use when starting significant work or breaking down complex tasks.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, TodoWrite]
---

# Planning in Small Increments

**All work must be done in small, known-good increments.** Each increment leaves the codebase in a working state.
**Document Management:** Use the plan-executor agent to create and maintain planning documents (PLAN.md, WIP.md, LEARNINGS.md).

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
        │                         │                         │
        │                         │                         │
        └─────────────────────────┴─────────────────────────┘
                                  │
                                  ▼
                         END OF FEATURE
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
              DELETE all              Merge LEARNINGS into:
              three docs              - CLAUDE.md (gotchas, patterns)
                                      - ADRs (architectural decisions)
```

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

### Why Wait for Approval?

- User maintains control of git history
- Opportunity to review before commit
- Prevents accidental commits of incomplete work
- Creates natural checkpoint for discussion

## PLAN.md Structure

```markdown
# Plan: [Feature Name]

## Goal

[One sentence describing the outcome]

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Steps

### Step 1: [One sentence description]

**Implementation**: What code will we write?
**Testing**: What needs testing? (if critical/complex)
**Done when**: How do we know it's complete?

### Step 2: [One sentence description]

**Implementation**: ...
**Testing**: ...
**Done when**: ...

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

🔨 IMPLEMENTING - Writing code
🧪 TESTING - Writing/running tests
🔍 REVIEWING - Checking quality
⏸️ WAITING - Awaiting commit approval
✅ COMPLETE - Step finished

## Progress

- [x] Step 1: [Description] ✓
- [x] Step 2: [Description] ✓
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

### [Title]

- **Context**: When this occurs
- **Issue**: What goes wrong
- **Solution**: How to handle it

## Patterns That Worked

### [Title]

- **What**: Description
- **Why it works**: Rationale
- **Example**: Brief code example

## Decisions Made

### [Title]

- **Options considered**: What we evaluated
- **Decision**: What we chose
- **Rationale**: Why
- **Trade-offs**: What we gained/lost

## Edge Cases

- [Edge case 1]: How we handled it
- [Edge case 2]: How we handled it

## Technical Debt

- [Item 1]: What was compromised and why
- [Item 2]: Future improvements needed
```

### Capture Learnings As They Occur

Don't wait until the end. When you discover something:

1. Add it to LEARNINGS.md immediately
2. Continue with current work
3. At end of feature, learnings are ready to merge

## Workflow Example

```
START FEATURE
│
├─► Create PLAN.md (get approval)
├─► Create WIP.md
├─► Create LEARNINGS.md
│
│   FOR EACH STEP:
│   │
│   ├─► Update WIP.md (status: IMPLEMENTING)
│   ├─► Write implementation
│   ├─► Add tests if critical/complex
│   ├─► Verify system works
│   ├─► Update WIP.md (status: REVIEWING)
│   ├─► Run quality checks
│   ├─► Capture learnings
│   ├─► Update WIP.md (status: WAITING)
│   └─► **WAIT FOR COMMIT APPROVAL**
│
END FEATURE
│
├─► Verify all criteria met
├─► Merge learnings into permanent locations
└─► Delete PLAN.md, WIP.md, LEARNINGS.md
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
git add -A
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

- Can I describe this in one sentence? ✓
- Can I do this in one session? ✓
- Will the system still work after? ✓
- Is it obvious when I'm done? ✓

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

### Updating the Plan

After a spike, you may need to update subsequent steps:

1. Document findings in LEARNINGS.md
2. Propose plan changes based on findings
3. Get approval for updated plan
4. Continue with revised steps

## Anti-Patterns

❌ **Committing without approval**

- Always wait for explicit "yes" before committing

❌ **Steps that span multiple commits**

- Break down further until one step = one commit

❌ **Vague "done when" criteria**

- "When it works" is not specific enough
- Be concrete: "When users can log in with Google and existing tests pass"

❌ **Letting WIP.md become stale**

- Update immediately when reality changes

❌ **Waiting until end to capture learnings**

- Add to LEARNINGS.md as discoveries occur

❌ **Plans that change silently**

- All plan changes require discussion and approval

❌ **Keeping planning docs after feature complete**

- Delete them; knowledge is now in permanent locations

❌ **Skipping tests for complex logic**

- Critical and complex components need tests
- Don't defer testing indefinitely

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

**Use TodoWrite for simple multi-step tasks instead.**

## Integration with TodoWrite

**PLAN.md vs TodoWrite:**

| Use PLAN.md when: | Use TodoWrite when: |
|-------------------|---------------------|
| Multi-session feature | Single-session task |
| Need to capture learnings | Simple checklist |
| Complex dependencies | Independent tasks |
| Requirements may evolve | Clear requirements |
| Need approval for plan changes | Straightforward execution |

**Can use both**: TodoWrite tracks current session's micro-tasks, PLAN.md tracks overall feature steps.

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
