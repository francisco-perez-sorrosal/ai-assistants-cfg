---
id: dec-052
title: Duration-aware OTel spans with openinference-standard attribution and parallel-execution markers
status: accepted
category: architectural
date: 2026-04-17
summary: Replace instant create-and-end spans with open-then-close pairs, add openinference-standard attributes, and mint fork_group UUIDs so Phoenix can show real durations and parallel subagent fan-outs.
tags:
  - observability
  - otel
  - phoenix
  - telemetry
  - openinference
  - parallel-execution
made_by: user
pipeline_tier: standard
affected_files:
  - task-chronograph-mcp/src/task_chronograph_mcp/events.py
  - task-chronograph-mcp/src/task_chronograph_mcp/otel_relay.py
  - task-chronograph-mcp/src/task_chronograph_mcp/server.py
  - hooks/send_event.py
  - hooks/hooks.json
  - eval/requirements.txt
---

## Context

`task-chronograph-mcp` currently relays Claude Code hook events to Phoenix as
OTel spans, but the span model has three structural deficits that starve
Phoenix's native aggregations:

1. **Zero-width spans.** Every span is created and immediately ended
   (`span.end()` on the next line of `start_span()`). `start_time` and
   `end_time` collapse to the same instant, so Phoenix's latency histograms,
   session duration sums, and span-sort-by-duration all show zero.
   `praxion.duration_s` is only set on the session-summary span, which
   isn't visible to per-span aggregations.
2. **Missing openinference-standard attributes.** Phoenix's built-in
   session views aggregate `llm.token_count.*`, `llm.cost.*`,
   `tool.description`, `tool.id`, and `user.id`. We emit `praxion.*`
   custom keys and `tool.name` but none of the attributes Phoenix
   natively dashboards. Cost and token reporting are therefore invisible
   even when they exist in upstream data (subagent transcript files
   contain `usage.input_tokens`/`usage.output_tokens`).
3. **No parallel-execution signal.** OpenInference's convention for
   parallel tool calls is distinct `tool_call.id` values inside a single
   parent LLM span's `message.tool_calls` list. We don't emit LLM spans.
   When the main agent spawns N subagents concurrently, the N
   `SubagentStart` events are distinguishable only by `agent_id`; no
   attribute says "these are siblings from the same delegation turn",
   so Phoenix cannot group them as a parallel fan-out.

Observability is gated by `PRAXION_DISABLE_OBSERVABILITY` which is
currently `1` in `.claude/settings.json` for this project, so this
decision ships the mechanism without immediately affecting live
telemetry volume.

## Decision

Adopt a three-phase telemetry model change:

**Phase 2 (this decision's primary scope) -- duration-aware tool spans.**
Open tool spans at `PreToolUse` and close them at `PostToolUse`
(or `PostToolUseFailure`). Correlation key is Claude Code's `tool_use_id`,
which appears in both hook payloads. Fall back to an instant-span emission
path when `tool_use_id` is missing (older Claude versions, manual
event posts) so the ingest is backward compatible. Agent duration spans
follow the same pattern in a later phase -- scoped out of Phase 2 to
keep the blast radius small.

**Phase 3 -- openinference-standard attribution.** Extend tool spans
with `tool.id` (= `tool_use_id`), `tool.description` (when the
tool registry provides one), and `user.id` (from git identity at
session start). LLM-level attributes (`llm.token_count.*`,
`llm.model_name`, `llm.system`, `llm.provider`) are populated
post-hoc from parsed subagent transcripts at `SubagentStop`; Phoenix
computes cost locally from tokens + model name without any external
call.

**Phase 4 -- parallel-execution markers.** The main agent stamps a
`praxion.fork_group` UUID on every `AGENT_START` event emitted for
subagents spawned in the same turn, plus `praxion.sibling_index`
and `praxion.sibling_count`. This enables `WHERE praxion.fork_group = "..."`
queries in Phoenix to reveal parallel fan-outs as cohorts. A subset
of Tier B Praxion attributes (hook_event, pipeline_tier, git_sha)
ship in the same phase because they are one-line additions.

Span emission stays fail-open -- OTel errors never propagate into the
EventStore path.

## Considered Options

### A. Open-close spans with pair correlation (chosen)

- Spans are created at Start, held open during execution, and ended at Stop
- Explicit `start_time`/`end_time` on `span.start()` and `span.end()`
- Pair correlation via `tool_use_id` with fallback to instant spans
- Fork grouping via main-agent-side UUID mint

**Pros:** real durations in Phoenix, standard OTel pattern, parallel
visibility, backward-compatible via fallback path.
**Cons:** open spans need reaping on orphaned starts; Phoenix sees spans
only at close time (BatchSpanProcessor has 5s schedule_delay already so
end-user latency impact is minor); slightly more memory per in-flight
tool call.

### B. Infer duration from next event timestamp

- Keep emitting instant spans
- At query time, compute duration = `next_event.timestamp - this_event.timestamp`

**Pros:** zero code change to emission path.
**Cons:** requires custom Phoenix query logic; doesn't work for
parallel tool calls (multiple "next" events ambiguous); loses the
fundamental OTel duration semantic.

### C. Add duration as a span attribute, keep spans instant

- Compute duration server-side (EventStore has both Start and Stop events)
- Attach as `praxion.duration_ms` on the span
- Keep `start_time == end_time`

**Pros:** minimal change; no open-span reaping needed.
**Cons:** Phoenix's built-in latency histograms read `start_time`/`end_time`,
not custom attrs, so dashboards still show zero; only custom queries
benefit; we'd still need a second change to actually fix Phoenix UX.

### D. Event-based "span events" instead of span pairs

- Keep one span per tool call, add span events (`add_event`) for phase
  transitions and boundary markers

**Pros:** simpler model.
**Cons:** span events are an OTel sidecar; they don't contribute to
latency, don't appear in trace waterfalls as sub-spans, and Phoenix
sessions view doesn't aggregate them.

## Consequences

**Positive:**

- Phoenix's native session view finally shows real tool durations, per-tool
  latency histograms, and critical-path analysis.
- Parallel subagent fan-outs are queryable as `praxion.fork_group` cohorts.
- Phoenix can compute cost from tokens + model name (no explicit cost
  attrs we own; Phoenix owns the price table).
- `tool_use_id` as span attribute enables correlation with upstream
  Anthropic tool-use objects.
- Backward compatibility preserved: missing `tool_use_id` triggers the
  existing instant-span path.

**Negative:**

- Additional in-memory state (`_open_tool_spans` dict) with
  reaping cost. Bounded: reaper runs every 10s, prunes >60s idle.
- Phoenix sees ended tool spans only when the pair completes, not at
  start. BatchSpanProcessor already introduces 5s delay so observed
  latency difference is small, but not zero.
- Subagent transcript parsing for token counts is post-hoc and may add
  100-500ms at `SubagentStop`. Acceptable because the hook is `async: true`.

**Rollback:** each phase is a single git revert away. The fallback
instant-span path in Phase 2 means partial rollout (e.g., revert
Phase 3 but keep Phase 2) is supported.

## Phase Execution Order

1. **Phase 1 (done):** `arize-phoenix>=14.6` floor in `eval/requirements.txt`
   unlocks Sessions pagination + list-detail session turns + annotation CLI.
2. **Phase 2 (this ADR's primary scope):** PreToolUse registration,
   `EventType.TOOL_START`, `tool_use_id` plumbing, open-close tool
   span correlation. Tests for the correlation path and fallback path.
3. **Phase 3:** `tool.id`, `tool.description`, `user.id`, transcript-
   derived `llm.token_count.*` + `llm.model_name` at `SubagentStop`.
4. **Phase 4:** `praxion.fork_group` mint + `sibling_index`/`sibling_count`;
   Tier B attributes (`praxion.hook_event`, `praxion.pipeline_tier`,
   `praxion.git_sha`).
5. **Docs phase:** user-facing observability README section; dead-code
   cleanup in `events.py` (`COMMAND_USE` emitter path is unreachable per
   the earlier chronograph audit).

Phase-by-phase execution with pause-for-review between phases, per the
agreed cadence. Each phase lands as one commit on
`worktree-telemetry-rollout`.

## Cost/Privacy Knobs

Documented in the observability README (Phase 5 docs):

- **Keep `llm.token_count.*`, let Phoenix compute cost locally** (default)
- **Env flag `CHRONOGRAPH_STRIP_LLM_ATTRS=1`** -- suppress LLM attribute
  emission for users who want pure structural telemetry without model
  metadata
- **Phoenix settings toggle** -- disable the PXI assistant chatbot if the
  user doesn't want Phoenix making its own LLM calls against a configured
  API key (separate from our span attributes, which cost nothing to emit)

None of the span attributes trigger external API calls or billing.
The only cost-moving surfaces in the Phoenix orbit are (a) the PXI
assistant chatbot, which is user-opted-in, and (b) evaluator scripts
like `trajectory_eval.py`, which users run explicitly.
