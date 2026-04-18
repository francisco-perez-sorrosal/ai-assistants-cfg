# Greenfield Project Onboarding

Reference for `new_cc_project.sh` and the `/new-cc-project` slash command — the entry point that turns an empty directory into a Claude-ready Python project with a per-run `onboarding_for_mushi_busy_ppl.md` trail map.

The script lays a minimal pre-Claude scaffold (`.git/`, `.gitignore`, empty `.claude/`), validates host prereqs, then `exec`s an interactive Claude Code session pre-seeded with `/new-cc-project`. Claude generates the source files (default: a mini coding agent + FastAPI web layer + smoke test), fetches current SDK signatures via `external-api-docs` instead of using stale training data, runs the test gate, and stages the scaffold for your first commit via `/co`.

For the design rationale, see [Design decision](#design-decision). For the slash command's full contract, read `commands/new-cc-project.md`.

## Contents

- [Prereqs](#prereqs)
- [How to run it](#how-to-run-it)
- [Expected prompt flow](#expected-prompt-flow)
- [What gets created](#what-gets-created)
- [Troubleshooting](#troubleshooting)
- [Design decision](#design-decision)
- [Limits for v1](#limits-for-v1)

## Prereqs

- `claude` binary on PATH — install Claude Code from `https://claude.com/product/claude-code`
- `i-am` plugin installed in the user-scope plugin registry — one-time `./install.sh code` from this Praxion checkout
- `git` on PATH
- `uv` (optional, recommended) — install with `curl -LsSf https://astral.sh/uv/install.sh | sh`. If absent, the test gate is skipped with a one-line install hint; the rest of the flow still works.

## How to run it

Two equivalent invocations:

```bash
# From the Praxion checkout
./new_cc_project.sh my-app

# From anywhere, after './install.sh code' has symlinked the entry into ~/.local/bin/
new-cc-project my-app
```

Optional second positional `[target-dir]` (defaults to `$PWD`) controls where `<project-name>/` is created:

```bash
new-cc-project my-app ~/code        # creates ~/code/my-app/
```

The script refuses to run if the project name does not match `^[A-Za-z0-9][A-Za-z0-9._-]*$` (letters/digits first, then letters/digits/`.`/`_`/`-`) or if the target path already exists and is non-empty.

## Expected prompt flow

The transcript below is illustrative — actual output depends on the installed Claude Code version, the current Claude Agent SDK doc, and the just-fetched `uv` defaults.

```text
# illustrative; actual output will differ
$ new-cc-project my-app
→ Scaffolded my-app at /Users/you/code/my-app. Launching Claude Code with /new-cc-project ...

[Claude Code session starts]

Claude: I will set up your CLAUDE.md, then ask one question.
        (running /init ...)
        (appending Praxion ## Agent Pipeline block to CLAUDE.md)

Claude: What would you like to build? Press enter for the default
        (mini coding agent with web UI), or describe your own project.
> [enter]

Claude: Fetching current Claude Agent SDK + uv docs from context-hub
        (external-api-docs skill) so generated code matches the installed versions ...
        Generating src/agent/core.py, src/agent/tools.py, src/web/app.py,
        tests/test_agent.py, pyproject.toml, .env.example ...

Claude: Running test gate: uv sync && uv run pytest -q
        1 passed in 0.34s

Claude: Generated onboarding_for_mushi_busy_ppl.md (trail map for busy people).
        Scaffold staged. Run /co to make the first commit (or /cop for commit+push);
        both apply rules/swe/vcs/git-conventions.md automatically, so you don't
        hand-craft commit messages.
```

## What gets created

The bash layer creates the first three rows; Claude generates the rest. The mushi doc carries a richer "What got created" table built from a just-in-time `ls` of the actual scaffold — this table is the reference shape.

| Path | Purpose | When to edit it |
|------|---------|-----------------|
| `.git/` | Git repo metadata | Never directly — use `git` commands |
| `.gitignore` | Five-line AI-assistants block (`.ai-work/`, `.env*`, `.claude/settings.local.json`) | Append project-specific patterns; do not remove the AI-assistants block |
| `.claude/` | Empty directory marking this as a Claude Code project | Drop project-scoped Claude config here later (e.g., custom `settings.json`) |
| `CLAUDE.md` | Project-level Claude instructions; `/init` generates it, then `/new-cc-project` appends the Praxion `## Agent Pipeline` block | When project conventions, top-level layout, or pipeline expectations change |
| `pyproject.toml` | uv-managed project metadata + deps (`claude-agent-sdk`, `fastapi`, `sse-starlette`, `httpx`, `pytest`) | Whenever you add a dependency — let `uv add` write it |
| `src/agent/*` | Agent core (`core.py`), starter tools (`tools.py` — `read_file` + safe-listed `run_command`), prompts (`prompts.py`) | Add tools, change the system prompt, swap the agent loop |
| `src/web/*` | FastAPI POST `/chat` endpoint streaming SSE (`app.py`) + minimal chat UI (`static/index.html`) | Change the API surface or the UI |
| `tests/test_agent.py` | One smoke test — constructs the agent without hitting the network (uses the SDK's mock/stub hooks) | Add behavioral tests as you add features |
| `.env.example` | Lists `ANTHROPIC_API_KEY=` placeholder; copy to `.env` (gitignored) for live runs | When you add new env vars — keep `.env.example` in sync |
| `onboarding_for_mushi_busy_ppl.md` | Per-run trail map: TL;DR card, Mermaid happy-path diagram, "What got created" table, 5–7 lessons (`<details>` collapsibles), glossary, "what to read next" | Treat as run-specific output; regenerate by running `/new-cc-project` again in a fresh dir, or hand-edit lessons as the app evolves |

## Troubleshooting

The bash script uses distinct exit codes for each prereq failure so you can diagnose without reading the source. The slash command (Claude side) has two additional failure modes the bash layer cannot detect.

| Symptom | Cause | Fix |
|---------|-------|-----|
| Exit `2`, "Usage:" or "invalid project name" on stderr | Missing `<project-name>` arg, or name fails the `^[A-Za-z0-9][A-Za-z0-9._-]*$` regex | Pass `<project-name>` as the first positional; use letters/digits/`._-` only (cannot start with `.` or `-`) |
| Exit `3`, "'claude' binary not found in PATH" | Claude Code is not installed | Install Claude Code: `https://claude.com/product/claude-code`, then re-run |
| Exit `4`, "the 'i-am' plugin is not installed" | `~/.claude/plugins/installed_plugins.json` does not contain `i-am@bit-agora` | Run `./install.sh code` from this Praxion checkout once, then re-run |
| Exit `5`, "'git' not found in PATH" | `git` is not installed | Install git from your package manager (`brew install git`, `apt install git`, etc.) |
| Exit `6`, "already exists and is not empty" | `<target-dir>/<project-name>` is a non-empty path | Pick a different name, pass a different `[target-dir]`, or remove the existing directory |
| Claude session starts but `/new-cc-project` is not found | Plugin registered but command files are not symlinked into the active config | Re-run `./install.sh --relink code` to refresh plugin command links |
| `uv is not installed` printed; `uv sync && uv run pytest -q` skipped | `uv` not on PATH; the slash command degrades gracefully and continues | Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`, then run `uv sync && uv run pytest -q` from the project root manually |
| Slash command aborts with "doesn't look like a freshly-scaffolded Praxion greenfield project" | `/new-cc-project` was invoked outside a directory created by `new_cc_project.sh` (no `.git/`, missing AI-assistants `.gitignore`, non-empty `.claude/` or `src/`) | Run `new_cc_project.sh <name>` first; or, to onboard an existing project, use `/onboard-project` instead |

## Design decision

The greenfield onboarding feature ships **prose specifications + a discovery hook**, not code templates or pinned SDK signatures. The slash command tells Claude *what* to build (file structure, dependency directions, safety patterns) and mandates that Claude fetch current Claude Agent SDK and `uv` docs via the [`external-api-docs`](external-api-docs.md) skill at run time, so generated code matches the SDK release on the user's machine — not the version baked into Praxion's training data.

Full rationale, considered options, and trade-offs: [`dec-053` — Prompt-over-template discipline for greenfield project scaffolding](../.ai-state/decisions/053-prompt-over-template-greenfield-scaffold.md).

## Limits for v1

- **Claude Code only.** Cursor and Claude Desktop variants are deferred. The bash entry assumes a `claude` CLI binary; it is not portable to other Claude surfaces.
- **Default app is Python only** (`uv` + `claude-agent-sdk` + FastAPI). No JS/TS or other-language variants in the default branch.
- **Custom-app branch tailors only L1 + L2** of the lesson ladder; L3–L7 stay generic Praxion-ecosystem lessons. Tailored count is fixed at 2 regardless of ladder size (5–7 total).
- **Bash test (`tests/new_cc_project_test.sh`) is single-file**, runnable as `bash tests/new_cc_project_test.sh`. Not yet wired into a `Makefile` target or CI.
- **Plugin install is user-scope only.** The script checks `~/.claude/plugins/installed_plugins.json` for `i-am@bit-agora`; project-scope plugin install is not auto-detected. Re-run `./install.sh code` once per workstation.
