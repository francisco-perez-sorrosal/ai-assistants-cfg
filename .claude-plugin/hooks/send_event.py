#!/usr/bin/env python3
"""Forward Claude Code hook events to the Task Chronograph server via HTTP POST.
Exits 0 unconditionally -- must never block agent execution.
"""
import json, os, sys, urllib.request  # noqa: E401

PROGRESS_MARKER = "PROGRESS.md"
DEFAULT_PORT = 8765


def _build_event(data):
    """Map a Claude Code hook payload to a Task Chronograph event dict."""
    hook = data.get("hook_event_name", "")
    sid = data.get("session_id", "")
    aid = data.get("agent_id", "")

    if hook in ("SubagentStart", "SubagentStop"):
        agent = data.get("agent_type", "")
        is_start = hook == "SubagentStart"
        event = {
            "event_type": "agent_start" if is_start else "agent_stop",
            "agent_type": agent, "session_id": sid,
            "agent_id": aid, "parent_session_id": sid,
            "message": f"Agent {agent} {'started' if is_start else 'stopped'}",
        }
        transcript = data.get("agent_transcript_path", "")
        if transcript:
            event["metadata"] = {"agent_transcript_path": transcript}
        return event

    if hook == "PostToolUse":
        fp = data.get("tool_input", {}).get("file_path", "")
        return {
            "event_type": "phase_transition" if PROGRESS_MARKER in fp else "tool_use",
            "agent_type": "unknown", "session_id": sid,
            "message": f"Write to {fp}", "metadata": {"file_path": fp},
        }
    return None


def main():
    try:
        event = _build_event(json.loads(sys.stdin.read()))
        if event is None:
            return
        port = int(os.environ.get("CHRONOGRAPH_PORT", str(DEFAULT_PORT)))
        payload = json.dumps(event).encode()
        req = urllib.request.Request(
            f"http://localhost:{port}/api/events",
            data=payload, headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


if __name__ == "__main__":
    main()
