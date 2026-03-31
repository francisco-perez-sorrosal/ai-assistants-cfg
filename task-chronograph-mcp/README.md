# Task Chronograph

Agent pipeline observability for Praxion. Traces every session -- pipeline runs, native Claude Code agents, tool calls, decisions, and phase transitions -- via OpenTelemetry, with persistent storage in [Arize Phoenix](https://github.com/Arize-ai/phoenix).

Used by **Claude Code** (plugin) and **Cursor** (via `./install.sh cursor`).

## Architecture

A single MCP server process runs two transports in parallel:

```
Claude Code Hooks (stdlib, <100ms)
  SessionStart, SubagentStart, SubagentStop,
  PostToolUse, PostToolUseFailure, Stop
      │
      │  HTTP POST to localhost:8765/api/events
      ▼
┌─────────────────────────────┐        ┌─────────────────────┐
│ Chronograph MCP Server      │        │ Phoenix Daemon      │
│ (daemon thread: uvicorn)    │        │ (persistent, launchd)│
│                             │        │                     │
│ HTTP API: /api/events       │─OTLP──>│ localhost:6006      │
│ EventStore (in-memory)      │        │ ~/.phoenix/phoenix.db│
│ OTel Relay (otel_relay.py)  │        │ 90-day retention    │
│                             │        └─────────────────────┘
│ (main thread: mcp stdio)   │
│ MCP Tools:                  │
│   get_pipeline_status       │
│   get_agent_events          │
│   report_interaction        │
└─────────────────────────────┘
```

**Dual storage**: EventStore (in-memory) serves real-time MCP queries. Phoenix (SQLite) persists traces for historical analysis and visualization. Either can fail independently.

## Quick Start

The `i-am` plugin auto-registers the MCP server. Phoenix is installed separately:

```bash
phoenix-ctl install          # Install Phoenix daemon (~300MB)
open http://localhost:6006   # Trace UI
```

To run the chronograph standalone (without the plugin):

```bash
cd task-chronograph-mcp
uv run python -m task_chronograph_mcp
```

## Hook Events

8 hook events are registered, forwarding to `send_event.py`:

| Hook Event | Event Type | OTel Span |
|---|---|---|
| `SessionStart` | session_start | Root SESSION span (CHAIN) |
| `Stop` | session_stop | End SESSION span |
| `SubagentStart` | agent_start | AGENT child span |
| `SubagentStop` | agent_stop | End AGENT span |
| `PostToolUse` | tool_use | TOOL child span (all tools) |
| `PostToolUseFailure` | error | TOOL span with ERROR status |
| `PreToolUse` (Bash) | -- | Code quality gate (sync) |
| `PreCompact` | -- | Pipeline state snapshot (sync) |

PostToolUse additionally detects PROGRESS.md writes and emits phase_transition events.

The hook script uses only Python stdlib and exits 0 unconditionally -- it never blocks agent execution.

## MCP Tools

- **`get_pipeline_status`** -- current state of all agents, interaction timeline, and delegation hierarchy
- **`get_agent_events`** -- filtered event history for a specific agent (with optional label filter)
- **`report_interaction`** -- record an interaction between pipeline participants

## OTel Span Model

Traces use [OpenInference](https://github.com/Arize-ai/openinference) semantic conventions:

```
SESSION (CHAIN) ← root, trace_id from session_id hash
├── researcher (AGENT, origin: praxion)
│   ├── Read (TOOL)
│   ├── Bash (TOOL)
│   └── [event: phase_transition] Phase 2/5
├── general-purpose (AGENT, origin: claude-code)
│   └── Edit (TOOL)
└── verifier (AGENT, origin: praxion)
```

Key attributes: `praxion.agent_origin` (praxion vs claude-code), `praxion.trace_type` (pipeline vs native), `praxion.project_name` (multi-project isolation).

## Configuration

| Variable | Default | Description |
|---|---|---|
| `CHRONOGRAPH_PORT` | `8765` | Chronograph HTTP API port |
| `CHRONOGRAPH_WATCH_DIR` | *(unset)* | Directory for PROGRESS.md file watching |
| `PHOENIX_ENDPOINT` | `http://localhost:6006/v1/traces` | OTLP export target |
| `PHOENIX_PROJECT_NAME` | `praxion-default` | Fallback project name |
| `OTEL_ENABLED` | `true` | Set to `false` to disable OTel export |

## Development

```bash
cd task-chronograph-mcp
uv run python -m pytest -q    # 150 tests
uv run ruff check              # Lint
uv run ruff format             # Format
```
