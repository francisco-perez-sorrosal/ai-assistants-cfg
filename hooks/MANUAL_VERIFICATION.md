# MANUAL_VERIFICATION.md — td-034 Subagent Isolation

## 1. Purpose

Verify that `hooks/worktree_guard.py` fires correctly for `Write`/`Edit` calls
issued by a subagent spawned inside a rework worktree session and blocks writes
to paths outside that worktree root.

This document satisfies the Path B fallback of
`hooks/test_worktree_guard_subagent.py`: the automated Path A test is skipped
because the `Agent` tool is not callable from a pytest context.

**Risk level:** SHIP GATE — the rework loop must not ship until this verification
passes (or an explicit ADR amendment accepts the risk).

---

## 2. Setup

1. Create a test rework worktree:

   ```
   EnterWorktree(name: td-034-manual-test)
   ```

2. Inside the new worktree, create a fixture findings file:

   ```bash
   mkdir -p .ai-work/td-034-manual-test
   echo "# VERIFIER_FINDINGS.md stub" > .ai-work/td-034-manual-test/VERIFIER_FINDINGS.md
   ```

3. Create a target file **outside** the worktree — at an absolute path in the
   main repo or a sibling worktree.  For example:

   ```bash
   echo "original content" > /tmp/td-034-target.txt
   # OR use an actual file inside the main checkout, e.g.:
   #   <absolute-path-to-main-repo>/td-034-marker.txt
   ```

   Record the absolute path — you will pass it to the agent below.

---

## 3. Reproduction Steps

1. Open a fresh Claude Code session **inside** the rework worktree
   (e.g. `cd .claude/worktrees/td-034-manual-test && claude`).

2. Spawn a minimal subagent with instructions to edit a file **outside** the
   worktree root.  The `systems-architect` agent is a suitable choice.
   Pass the absolute path to avoid any relative-path ambiguity:

   ```
   Task slug: td-034-manual-test
   Spawn systems-architect with prompt:
     "Edit the file at <ABSOLUTE-PATH-TO-TARGET> and change its first line
      to 'mutated'.  Use the Edit tool with file_path set to the absolute
      path shown above."
   ```

3. Observe whether the PreToolUse hook (`hooks/worktree_guard.py`) fires.

---

## 4. Expected Outcome

The `worktree_guard.py` PreToolUse hook should intercept the `Edit` call and
exit with code `2` (BLOCKED).  Claude Code surfaces a hook-error message.
The expected stderr output from the guard is:

```
[worktree-guard] BLOCKED: cross-worktree write
[worktree-guard]   target:   <ABSOLUTE-PATH-TO-TARGET>
[worktree-guard]   session:  <worktree-root>
[worktree-guard]   resolves in different git tree: <main-repo-root>
[worktree-guard]   Rewrite the path to stay within the session worktree, or
[worktree-guard]   export PRAXION_DISABLE_WORKTREE_GUARD=1 if this is intentional.
```

The target file must remain **unmodified** (content still `"original content"`).

---

## 5. Recording the Verification

Append a row to `.ai-work/verifier-rework-loop/TEST_RESULTS.md`:

```
[<ISO-8601-datetime>] [manual] td-034 verification: PASSED — guard fired on
<date> with operator <your-github-handle>
```

---

## 6. Failure Mode

If the guard does **not** fire (the agent edits the target file successfully),
this is a **SHIP BLOCKER** per the rework-loop isolation contract.

Required next steps on failure:
1. Record `FAIL` in `TEST_RESULTS.md` with verbatim agent output.
2. Do NOT proceed to Group G.
3. Either fix `hooks/worktree_guard.py` to fire correctly for subagent sessions,
   OR obtain an explicit user ADR amendment accepting the risk with rationale
   before shipping the rework feature.
