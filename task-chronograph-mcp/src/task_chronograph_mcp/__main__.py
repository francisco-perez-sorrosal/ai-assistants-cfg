"""Hybrid stdio+HTTP entry point: MCP tools over stdio, dashboard over HTTP.

The plugin system auto-registers this as a stdio MCP server. On startup, the
HTTP server (dashboard + REST API + SSE) launches in a daemon thread so the
dashboard is available at http://127.0.0.1:<port> without manual setup.
"""

from __future__ import annotations

import asyncio
import os
import sys
import threading

import uvicorn

from task_chronograph_mcp.server import DEFAULT_PORT, _http_ready, app, mcp


def _run_http_server(port: int) -> None:
    """Run the Starlette app (dashboard + API) in its own event loop."""
    config = uvicorn.Config(
        app, host="127.0.0.1", port=port, log_level="warning", access_log=False,
    )
    server = uvicorn.Server(config)
    asyncio.run(server.serve())


port = int(os.environ.get("CHRONOGRAPH_PORT", str(DEFAULT_PORT)))

http_thread = threading.Thread(
    target=_run_http_server, args=(port,), daemon=True, name="chronograph-http",
)
http_thread.start()

if _http_ready.wait(timeout=5):
    sys.stderr.write(f"Task Chronograph dashboard: http://127.0.0.1:{port}\n")
else:
    sys.stderr.write("Task Chronograph: HTTP server failed to start — dashboard unavailable\n")

mcp.run()
