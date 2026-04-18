---
description: Scaffold a greenfield Claude-ready Python project and onboard it to Praxion.
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, mcp__chub__*]
---

Onboard the current (freshly scaffolded) directory into a Claude-ready Python project: run `/init`, append the Praxion Agent Pipeline block, ask one question, generate either a default mini coding agent or a custom app, generate a per-run `onboarding_for_mushi_busy_ppl.md` trail map, stage the scaffold for the user, and hand off to `/co`.

## Sections

1. §Guard — shape check before doing anything
2. §What is Praxion — canonical paragraph (sentinel-fenced, copied verbatim by the mushi doc)
3. §Default App Spec — the six-file seed app + invariants
4. §SDK smoke check — the import probe and doc-staleness recovery
5. §Init idempotency — predicate for appending the Agent Pipeline block
6. §Mushi Doc Spec — the seven ordered sections
7. §Five-to-Seven Lessons — L1–L7 canonical ladder (L6 mandatory, L7 optional)
8. §Custom-App Branch — how to tailor the ladder when the user describes their own app
9. §Prereq Behaviors — `uv` missing, `ANTHROPIC_API_KEY` unset
10. §Agent Pipeline Block — verbatim source

## §Guard

Before anything else, verify the filesystem shape. The bash layer is supposed to have left a scaffolded-but-empty directory — if any of these checks fail, print the guarded-abort message and stop.

Run these four checks from the project root:

1. `test -d .git` — the directory is a git repo.
2. `grep -q '^# AI assistants$' .gitignore && grep -q '^\.ai-work/$' .gitignore` — the AI-assistants block is present. (The bash layer wrote a 5-line `.gitignore` beginning with `# AI assistants`.)
3. `test -d .claude && [ -z "$(ls -A .claude 2>/dev/null)" ]` — `.claude/` exists and is empty.
4. `! test -e src || [ -z "$(ls -A src 2>/dev/null)" ]` — `src/` is absent, or is an empty directory.

If any check fails, abort with:

> This directory doesn't look like a freshly-scaffolded Praxion greenfield project. `/new-cc-project` expects to run inside a directory produced by `new_cc_project.sh` (a `.git/` repo with the AI-assistants `.gitignore` block, an empty `.claude/`, and no `src/` tree yet). If you meant to onboard an existing project, run `/onboard-project` instead.

Exit without writing anything.

## Flow

When the guard passes, follow these steps in order. Each step is a contract — Claude chooses tactics, but the shape is fixed.

1. **Invoke `/init`.** Let Claude Code analyze the (nearly empty) directory and generate `CLAUDE.md`. Do not author `CLAUDE.md` by hand.
2. **Append the Agent Pipeline block idempotently.** Per §Init idempotency, check whether `CLAUDE.md` already has a `## Agent Pipeline` heading. If not, append the block verbatim from §Agent Pipeline Block.
3. **Ask the single content question.** Use `AskUserQuestion` with the exact prompt: `What would you like to build? Press enter for the default (mini coding agent with web UI), or describe your own project.`
4. **Branch on the answer.**
   - Empty answer, or any of `default` / `yes` / `y` / `ok` (case-insensitive) → go to §Default App Spec.
   - Any other non-trivial description → go to §Custom-App Branch (which still reuses §Default App Spec's structural invariants; only L1 and L2 of the lesson ladder become tailored).
5. **Fetch current external API signatures FIRST.** Before generating any Python file, run `mcp__chub__chub_search` with queries `claude-agent-sdk python` and `uv python project init` (or equivalents surfaced by the search), then `mcp__chub__chub_get` to pull the current signatures and `pyproject.toml` conventions. Hold the fetched content in working memory; do NOT invent method names or parameter shapes from training data.
6. **Generate the source files** per §Default App Spec (or the tailored variant). Maintain the dependency-direction invariant: `src/agent/` imports nothing from `src/web/`.
7. **Run the SDK smoke check** per §SDK smoke check before writing `src/agent/core.py` if the fetched doc leaves any ambiguity about the import surface. If the probe fails, follow the recovery path in that section.
8. **Regenerate the `.gitignore` Python block.** Append (without duplicating) `__pycache__/`, `.venv/`, `*.egg-info/`, `.pytest_cache/`. Do NOT exclude `uv.lock` — it stays tracked.
9. **Run the test gate.** `uv sync && uv run pytest -q`. If `uv` is absent, see §Prereq Behaviors.
10. **Generate the mushi doc LAST.** File anchors (§Mushi Doc Spec L25) must be computed against the final on-disk state, so this step follows everything that writes source code.
11. **Stage the scaffold.** `git add -A` (the `.gitignore` keeps `.env` and `.ai-work/` out). Do NOT run `git commit` — that is the user's next move via `/co`.
12. **Print the exit handoff.** Verbatim wording in the Exit handoff section below.

## §What is Praxion

This is the canonical paragraph. It is enclosed between sentinel markers so the mushi-doc generation step can copy it verbatim by matching the markers. Do not paraphrase it into the mushi doc; copy the bytes between (but not including) the markers.

<!-- PRAXION-PARAGRAPH-START -->
Praxion is a toolbox that turns Claude Code into a disciplined engineering partner. It ships a curated set of skills, agents, rules, commands, and memory that wire Claude into a clean Understand → Plan → Verify workflow. As you work, the system researches external APIs, plans in small known-good increments, writes and runs tests, verifies its own output against acceptance criteria, and remembers what you've agreed on across sessions — so you spend your attention on deciding what to build next, not on hand-holding the tools.
<!-- PRAXION-PARAGRAPH-END -->

## §Default App Spec

Generate a six-file seed app: a minimal agent core, two starter tools, prompts, a thin FastAPI web layer, a smoke test, and the `pyproject.toml` / `.env.example` pair. Signature details come from the fetched chub docs — DO NOT hardcode SDK or `uv` surface from memory.

**File inventory (paths are mandatory):**

- `src/agent/__init__.py` — package marker.
- `src/agent/core.py` — agent entry point; uses symbols from `claude_agent_sdk` (or the current equivalent module path obtained from chub). Exports one constructor/factory that downstream code (tests, web) imports.
- `src/agent/tools.py` — registers exactly two tools: `read_file(path: str) -> str` and `run_command(cmd: str) -> str`. See the safe-list invariant below.
- `src/agent/prompts.py` — system prompt(s) for the agent; plain-text constants.
- `src/web/__init__.py` — package marker.
- `src/web/app.py` — FastAPI app exposing POST `/chat` that streams agent output as SSE. Imports the agent entry from `src.agent.core`.
- `src/web/static/index.html` — minimal chat UI that POSTs to `/chat` and renders the SSE stream.
- `tests/__init__.py` — package marker.
- `tests/test_agent.py` — one smoke test; constructs the agent and asserts it initializes without hitting the network (use the SDK's mock/stub hooks per the fetched doc).
- `pyproject.toml` — `[project]` with name/version/python-requires, deps: `claude-agent-sdk`, `fastapi`, `sse-starlette` (or equivalent from fetched docs), `httpx`, `pytest`; `[tool.uv]` per current uv conventions.
- `.env.example` — lists `ANTHROPIC_API_KEY=` (empty value placeholder).

**Dependency-direction invariant:** `src/agent/` imports nothing from `src/web/`. `src/web/` may import from `src/agent/`. Verify with `grep -r 'from src.web\|import src.web' src/agent/` returning zero matches before finishing (AC6).

**Safe-list invariant for `run_command`:** `src/agent/tools.py` defines a module-scope constant `SAFE_COMMANDS = frozenset({"ls", "pwd", "cat", "python"})`. `run_command` splits the input string on whitespace, takes the first token, and compares it against `SAFE_COMMANDS`. Any other first token returns a clear refusal string (a plain `str` return; do not raise). The frozenset must be at module scope (not inside the function) so the invariant reads at a glance.

**FastAPI `/chat` shape:** POST accepting a JSON body with at minimum `{"message": str}`. Response is `text/event-stream` streaming tokens from the agent. Use whatever streaming primitive the fetched FastAPI/sse-starlette doc recommends.

**Smoke test:** `tests/test_agent.py` imports the agent factory from `src.agent.core`, constructs it, and asserts it is not `None` — using the SDK's in-process mock hook if the fetched doc describes one, otherwise asserting construction-without-network via a stubbed/patched transport. The test must pass under `uv run pytest -q` with only `ANTHROPIC_API_KEY` (optionally) set.

**No `.ai-state/` writes:** this command does NOT create `.ai-state/decisions/`, `.ai-state/ARCHITECTURE.md`, or `.ai-state/specs/` inside the new project. Those directories are owned by pipeline agents (systems-architect, etc.) and are created lazily when the user runs a real pipeline later.

## §SDK smoke check

After `uv add claude-agent-sdk` succeeds, before or immediately after writing `src/agent/core.py`, probe the import surface with a one-liner:

```
uv run python -c "from claude_agent_sdk import ClaudeSDKClient, query, tool; print('ok')"
```

If it prints `ok`, proceed.

If the import fails with `ImportError` / `ModuleNotFoundError` / `AttributeError` on one of those symbols, it means the fetched chub doc is referencing symbol names that drifted in the installed SDK. Recovery path:

1. Re-read the fetched chub doc entry — the search in step 5 of §Flow may have returned an older version; request the entry id again and prefer entries marked `official` or `maintainer`.
2. Inspect the installed package: `uv run python -c "import claude_agent_sdk; print(dir(claude_agent_sdk))"` and pick the actually-present public symbols.
3. Regenerate `src/agent/core.py` against those symbols.
4. Submit `chub_feedback` with `vote: "down"`, `label: "outdated"`, and a comment naming the missing symbol and the installed SDK version so the next user inherits a corrected doc. Append the identity suffix per the `external-api-docs` skill (derive from `git config --get user.name` / `user.email`).

Never copy symbol names from this file into generated code — this file deliberately does not pin them. The smoke-check line is a probe, not a signature reference.

## §Init idempotency

Before appending the §Agent Pipeline Block to `CLAUDE.md`, run:

```
grep -q '^## Agent Pipeline' CLAUDE.md
```

- Exit `0` (match found) → the block already exists from a prior `/new-cc-project` or `/onboard-project` run. Skip the append.
- Exit non-zero (no match) → append the block verbatim from §Agent Pipeline Block.

This predicate mirrors the idempotency check in `/onboard-project`, so re-running either command does not duplicate the section.

## §Mushi Doc Spec

Generate `<project-root>/onboarding_for_mushi_busy_ppl.md` with these seven sections in this exact order:

1. **Canonical Praxion paragraph** — copied verbatim (byte-for-byte) from between the `PRAXION-PARAGRAPH-START` and `PRAXION-PARAGRAPH-END` sentinel HTML-comment markers in §What is Praxion. Do not paraphrase. Do not re-wrap.
2. **TL;DR card** — exactly three lines; one each for "what you have", "what you can do right now", "what to do next".
3. **Mermaid happy-path diagram** — ≤10 nodes, conforming to `rules/writing/diagram-conventions.md`. One concept only (e.g., user → web → agent → SDK).
4. **What got created table** — columns `Artifact | Purpose | Edit when…`. One row per generated file. **Just-in-time verification:** before finalising the table, `ls -la <path>` every row's artifact; if any path does not resolve, remove the row or fix the path — do not ship a row that does not exist on disk. The mushi doc and the scaffold must agree on the same run.
5. **Five-to-seven lesson ladder** — `<details>` collapsibles, one per lesson. Use the canonical L1–L7 from §Five-to-Seven Lessons. L6 is mandatory. L1, L2, and L7 may be omitted only if anchor generation fails for them (final ladder is never below 5).
6. **Glossary collapsible** — one `<details>` block with short definitions for terms the mushi doc uses: Praxion, skill, agent, rule, command, the Understand/Plan/Verify methodology, Claude Agent SDK, uv, the `/co` and `/cop` commands.
7. **What to read next** — a one-line pointer to `docs/project-onboarding.md` in the Praxion repo, plus the AC16 explainer: "Run `/co` to make your first commit (or `/cop` for commit+push); both apply `rules/swe/vcs/git-conventions.md` automatically, so you don't hand-craft commit messages."

**File anchors:** every lesson references at least one concrete anchor of the form `src/<path>:<line>` that resolves to a real line in the final scaffold. Generate the mushi doc after all source files are written so anchors are stable. If a line reference shifts during a late edit, regenerate it before finalising.

## §Five-to-Seven Lessons

Canonical ladder. Ship all seven by default; if anchor generation fails for L2 or L7, they may be omitted (final ladder is never below 5). L6 is mandatory.

Each lesson has four bullets:
- **What you'll learn** — the competency the lesson unlocks.
- **Command to run** — the Praxion slash command or skill the lesson exercises.
- **Expected outcome** — what success looks like.
- **Try it on** — a concrete anchor in the scaffold (e.g., `src/agent/tools.py:<line>`).

### L1 — Add a new tool to the agent

- **What you'll learn:** the three-document planning model for any change bigger than a one-liner.
- **Command to run:** `/software-planning` (creates `IMPLEMENTATION_PLAN.md`, `WIP.md`, `LEARNINGS.md` under `.ai-work/<task-slug>/`).
- **Expected outcome:** a plan with 2–4 known-good steps; tests first; then code; then verification.
- **Try it on:** add `list_dir(path: str) -> str` next to `read_file` in `src/agent/tools.py:<line-of-SAFE_COMMANDS>`.

### L2 — Refactor the web layer safely

- **What you'll learn:** how to change code structure without changing behavior, inside an isolated worktree.
- **Command to run:** `/create-worktree` to branch off; then the `refactoring` skill to plan the split.
- **Expected outcome:** `src/web/app.py` split into a route module and an SSE-streaming helper, with the test still green.
- **Try it on:** `src/web/app.py:<line-of-POST-chat-route>`.

### L3 — Look up Claude Agent SDK docs

- **What you'll learn:** never guess an SDK signature; fetch the current doc first.
- **Command to run:** spawn the `researcher` agent, or directly invoke the `external-api-docs` skill via `mcp__chub__chub_search` + `mcp__chub__chub_get`.
- **Expected outcome:** a documented diff between what the installed SDK exposes and what any prose in this project references.
- **Try it on:** `src/agent/core.py:<line-of-import>`.

### L4 — Add a feature with quality gates

- **What you'll learn:** the full Standard-tier pipeline (researcher → systems-architect → implementation-planner → implementer + test-engineer → verifier).
- **Command to run:** describe the feature to Claude; Claude spawns the agents in order.
- **Expected outcome:** `SYSTEMS_PLAN.md`, `IMPLEMENTATION_PLAN.md`, code, tests, `VERIFICATION_REPORT.md` — all in `.ai-work/<task-slug>/`.
- **Try it on:** add an auth gate in front of POST `/chat` in `src/web/app.py:<line-of-POST-chat-route>`.

### L5 — Persist a project decision

- **What you'll learn:** how to turn a meaningful decision into a durable ADR.
- **Command to run:** `/cajalogic` (and follow `rules/swe/adr-conventions.md`).
- **Expected outcome:** a new numbered ADR under `.ai-state/decisions/` with YAML frontmatter and MADR body sections; `DECISIONS_INDEX.md` regenerated.
- **Try it on:** record "chose SSE over WebSockets for POST /chat streaming" as an ADR; anchor in `src/web/app.py:<line-of-streaming-return>`.

### L6 — Testing workflow (MANDATORY)

- **What you'll learn:** Praxion's testing rhythm — behavioral tests designed first, implementation follows, the full suite runs green before commit.
- **Command to run:** `/test` (applies the `testing-strategy` skill; writes tests from acceptance criteria and runs the suite).
- **Expected outcome:** new behavioral tests in `tests/`, all passing under `uv run pytest -q`.
- **Try it on:** extend the smoke test at `tests/test_agent.py:<line-of-test-fn>` — add a case that asserts `run_command("rm -rf /")` returns the refusal string (safe-list invariant).

### L7 — Project exploration as code grows (OPTIONAL)

- **What you'll learn:** how to orient yourself in the project once the seed shape has grown; produce an up-to-date architecture view without reading every file.
- **Command to run:** `/explore-project` (applies the `project-exploration` skill).
- **Expected outcome:** a current map of modules, entry points, and external dependencies — useful once you have a dozen files or more.
- **Try it on:** run it once the default app has grown past the seed files; anchor on any module that did not exist at scaffold time.

## §Custom-App Branch

When the user's answer is a non-trivial description of a different app (not empty, not "default"), still run every step of §Flow — only the two tailored lesson slots change.

**Rule:** the ladder stays at 5–7 lessons. **L1 and L2 are the tailored slots** — adapt them to the user's actual app (e.g., if the user described a Discord bot, L1 becomes "add a new slash command", L2 becomes "refactor the event dispatcher"). **L3, L4, L5, L6, and (optional) L7 remain generic** — they are Praxion-ecosystem lessons and apply regardless of the app.

Count contract: **2 tailored + (3–5) generic = 5–7 total.** Tailored count is fixed at 2; generic count follows the overall ladder size (L7 is optional). If Claude cannot produce a concrete `src/<path>:<line>` anchor for a tailored lesson (e.g., the user described a Haskell library — no `src/` tree), fall back to the generic L1/L2 from §Five-to-Seven Lessons and note the fallback in the mushi doc's troubleshooting line.

The canonical Praxion paragraph, the default mushi-doc structure, and the exit handoff are all unchanged in the custom branch.

## §Prereq Behaviors

**`uv` missing.** Before running the test gate, check `command -v uv`. If absent:

- Print a one-line install hint: `uv is not installed. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh (then re-run 'uv sync && uv run pytest -q' from this project root).`
- Skip `uv sync` and `uv run pytest -q`. Do not fail the session.
- Note the skipped step in the mushi doc's "What to do next": add a bullet `Install uv, then run: uv sync && uv run pytest -q` above the `/co` line.

**`ANTHROPIC_API_KEY` unset.** Do NOT block the flow. The smoke test is written to pass without the key (constructs the agent against a mock transport). Handle it this way:

- `.env.example` lists `ANTHROPIC_API_KEY=` as a placeholder.
- The mushi doc's "What to do next" mentions that live agent calls require `export ANTHROPIC_API_KEY=sk-ant-...` in a `.env` file (which is gitignored) before running `uv run python -m src.web.app`.

## §Agent Pipeline Block

Append this block to `CLAUDE.md` when the idempotency predicate (§Init idempotency) reports no existing heading. **Source of truth:** the identical block lives in `commands/onboard-project.md`. If that file changes, mirror the change here — both commands must produce byte-identical CLAUDE.md sections.

```markdown
## Agent Pipeline

Follow the Understand, Plan, Verify methodology. For multi-step work (Standard/Full tier), delegate to specialized agents in pipeline order. Each pipeline operates in an ephemeral `.ai-work/<task-slug>/` directory (deleted after use); permanent artifacts go to `.ai-state/` (committed to git).

1. **researcher** → `.ai-work/<slug>/RESEARCH_FINDINGS.md` — codebase exploration, external docs
2. **systems-architect** → `.ai-work/<slug>/SYSTEMS_PLAN.md` (ephemeral feature plan) + `.ai-state/decisions/` (permanent ADRs) + `.ai-state/ARCHITECTURE.md` + `docs/architecture.md` (permanent architecture docs)
3. **implementation-planner** → `.ai-work/<slug>/IMPLEMENTATION_PLAN.md` + `WIP.md` — step decomposition
4. **implementer** + **test-engineer** (concurrent) → code + tests — execute steps from the plan
5. **verifier** → `.ai-work/<slug>/VERIFICATION_REPORT.md` — post-implementation review

Always include expected deliverables when delegating to an agent. The agent coordination protocol rule has full delegation checklists.
```

## Test gate

After all files are generated and before the mushi doc is finalised, run:

```
uv sync && uv run pytest -q
```

If `uv` is absent, see §Prereq Behaviors and skip gracefully. If tests fail, surface the output to the user — do not silently hide a red test. The mushi doc notes the failure in "What to do next".

## Exit handoff

Stage everything (`git add -A`, honoring the `.gitignore` that keeps `.env` and `.ai-work/` out). Do NOT commit. Print exactly:

```
Scaffold staged. Run /co to make the first commit (or /cop for commit+push); both apply rules/swe/vcs/git-conventions.md automatically, so you don't hand-craft commit messages.
```

The mushi doc's "What to do next" one-liner carries the same language (AC16) — point at `/co` as default, mention `/cop` as the commit-and-push alternative, and state explicitly that the user is outsourcing commit-message authoring to the git-conventions rule.
