# Task Chronograph

Real-time observability for Claude Code agent pipelines. The web dashboard shows an **interaction timeline** -- the full story of what happens between a user query and the final response, with all delegations, results, and decisions visible -- alongside **agent status cards** tracking each agent's phase progress and health.

## Quick Start

The `i-am` plugin auto-registers the MCP server on install. The dashboard starts automatically at `http://localhost:8765` — no manual setup required.

To run the server standalone (without the plugin):

```bash
cd task-chronograph-mcp
uv run python -m task_chronograph_mcp
```

## Hook Setup

Hooks forward `SubagentStart`, `SubagentStop`, and `PostToolUse` (Write) events to the chronograph server. Add the following to `.claude/settings.local.json` in your project:

```json
{
  "hooks": {
    "SubagentStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/ai-assistants/.claude-plugin/hooks/send_event.py",
            "timeout": 10,
            "async": true
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/ai-assistants/.claude-plugin/hooks/send_event.py",
            "timeout": 10,
            "async": true
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/ai-assistants/.claude-plugin/hooks/send_event.py",
            "timeout": 10,
            "async": true
          }
        ]
      }
    ]
  }
}
```

Replace `/path/to/ai-assistants` with the absolute path to the `ai-assistants` repo.

The hook script uses only Python stdlib and exits 0 unconditionally -- it never blocks agent execution, even when the server is down.

## MCP Server Registration

The `i-am` plugin declares `mcpServers` in its manifest. Installing the plugin auto-registers everything — MCP tools via stdio **and** the web dashboard via a background HTTP server. No manual `claude mcp add` needed.

On startup, the entry point (`python -m task_chronograph_mcp`):

1. Launches the HTTP server (dashboard + REST API + SSE) in a daemon thread
2. Runs the MCP stdio transport in the main thread
3. Both share a single thread-safe `EventStore`

If the HTTP server fails to start (e.g., port conflict), MCP tools still work via stdio — the dashboard is unavailable but a warning is logged to stderr.

### MCP Tools

- **`get_pipeline_status`** -- current state of all agents, interaction timeline, and delegation hierarchy
- **`get_agent_events`** -- filtered event history for a specific agent (with optional label filter)
- **`report_interaction`** -- record an interaction between pipeline participants (query, delegation, result, decision, response)

## Architecture

A single process runs two transports in parallel:

```
plugin.json (mcpServers)
        │
        ▼
  __main__.py
   ├── daemon thread: uvicorn → Starlette app
   │     ├── /           dashboard (Jinja2 + htmx + SSE)
   │     ├── /api/*      event ingestion + state API
   │     └── /mcp        MCP streamable HTTP (bonus)
   │
   └── main thread: mcp.run() → stdio MCP transport
        │
        └── shared EventStore (thread-safe, threading.Lock)
```

The `EventStore` uses `threading.Lock` for data protection and `call_soon_threadsafe` for cross-thread SSE broadcasting. MCP tool calls from either transport read/write the same store.

### Event Sources

1. **Hooks** (primary) -- zero-token-cost event forwarding from `SubagentStart`, `SubagentStop`, and `PostToolUse` hooks configured in project settings. Events POST to the HTTP API.
2. **MCP tools** -- agents call `report_interaction` via stdio to record pipeline interactions
3. **PROGRESS.md file watcher** (fallback) -- watches `.ai-work/PROGRESS.md` for phase-transition lines appended by agents, covering subagent contexts where hooks may not fire

## Hook Payload Reference

Claude Code hook payloads differ from what some documentation suggests. Actual field names (verified in v2.1.37):

| Hook Event | Key Fields |
| ---------- | ---------- |
| `SubagentStart` | `session_id` (parent session), `agent_id` (subagent), `agent_type` (e.g., `"general-purpose"`, `"i-am:researcher"`) |
| `SubagentStop` | Same as start, plus `agent_transcript_path` |
| `PostToolUse` | `session_id`, `tool_input` (contains `file_path` for Write tool) |

Notably: `session_id` is the **parent** session that spawned the subagent (there is no separate `parent_session_id` field), and the agent type field is `agent_type` (not `subagent_type`).

## Interaction Types

The interaction timeline uses `report_interaction` entries to reconstruct the pipeline story. Each interaction has a type that determines its dashboard badge color:

| Type | Color | Meaning |
| ---- | ----- | ------- |
| `query` | Purple | User asks the main agent something |
| `delegation` | Blue | Main agent delegates to a subagent |
| `result` | Green | Agent returns findings |
| `decision` | Yellow | Main agent makes a routing decision |
| `response` | Teal | Main agent responds to the user |
| *(unknown)* | Gray | Any other type (extensible) |

Only `delegation` interactions contribute to the agent hierarchy. Unknown types are accepted and rendered with a generic badge.

## Configuration

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `CHRONOGRAPH_PORT` | `8765` | Server port (used by both the server and the hook script) |
| `CHRONOGRAPH_WATCH_DIR` | *(unset)* | Directory containing `.ai-work/PROGRESS.md` to watch (e.g., the project root). File watching is disabled when unset. |

## Development

Run tests:

```bash
cd task-chronograph-mcp
uv run pytest -v
```
