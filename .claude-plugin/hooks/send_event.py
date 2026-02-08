#!/usr/bin/env python3
"""Forward Claude Code hook events to the Task Chronograph server via HTTP POST.
Exits 0 unconditionally -- must never block agent execution.
"""
import json, os, re, sys, urllib.request  # noqa: E401

PROGRESS_MARKER = "PROGRESS.md"
DEFAULT_PORT = 8765

PROGRESS_LINE_RE = re.compile(
    r"\[([^\]]+)\]\s+\[([^\]]+)\]\s+(?:Phase\s+(\d+)/(\d+):\s+(\S+)\s+--\s+)?(.+)"
)


def _post(port, path, payload):
    """POST JSON to the Chronograph server. Swallow all errors."""
    try:
        req = urllib.request.Request(
            f"http://localhost:{port}{path}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


def _parse_last_progress_line(content):
    """Parse the last non-empty line from PROGRESS.md content."""
    lines = [l for l in content.strip().splitlines() if l.strip()]
    if not lines:
        return None
    match = PROGRESS_LINE_RE.match(lines[-1].strip())
    if not match:
        return None
    ts, agent, phase, total, phase_name, rest = match.groups()
    return {
        "agent_type": agent,
        "phase": int(phase) if phase else 0,
        "total_phases": int(total) if total else 0,
        "phase_name": phase_name or "",
        "message": rest.split("#")[0].strip(),
    }


def _agent_label(data):
    """Best available human-readable label for the agent in this hook payload."""
    return data.get("agent_type", "") or data.get("agent_id", "") or "unknown"


def _build_events(data):
    """Map a Claude Code hook payload to Chronograph events + interactions."""
    hook = data.get("hook_event_name", "")
    sid = data.get("session_id", "")
    aid = data.get("agent_id", "")
    events = []
    interactions = []

    if hook == "SubagentStart":
        agent = data.get("agent_type", "")
        label = _agent_label(data)
        events.append({
            "event_type": "agent_start",
            "agent_type": agent or label, "session_id": sid,
            "agent_id": aid, "parent_session_id": sid,
            "message": f"Agent {label} started",
        })
        interactions.append({
            "source": "main_agent", "target": aid or agent or label,
            "summary": f"Delegated to {label}",
            "interaction_type": "delegation",
        })

    elif hook == "SubagentStop":
        agent = data.get("agent_type", "")
        label = _agent_label(data)
        events.append({
            "event_type": "agent_stop",
            "agent_type": agent or label, "session_id": sid,
            "agent_id": aid, "parent_session_id": sid,
            "message": f"Agent {label} stopped",
        })
        transcript = data.get("agent_transcript_path", "")
        if transcript:
            events[-1]["metadata"] = {"agent_transcript_path": transcript}
        interactions.append({
            "source": aid or agent or label, "target": "main_agent",
            "summary": f"{label} returned results",
            "interaction_type": "result",
        })

    elif hook == "PostToolUse":
        fp = data.get("tool_input", {}).get("file_path", "")
        if PROGRESS_MARKER in fp:
            content = data.get("tool_input", {}).get("content", "")
            if not content:
                content = data.get("tool_input", {}).get("new_string", "")
            parsed = _parse_last_progress_line(content) if content else None
            if parsed:
                events.append({
                    "event_type": "phase_transition",
                    "agent_type": parsed["agent_type"],
                    "agent_id": aid, "session_id": sid,
                    "phase": parsed["phase"],
                    "total_phases": parsed["total_phases"],
                    "phase_name": parsed["phase_name"],
                    "message": parsed["message"],
                })
            else:
                events.append({
                    "event_type": "phase_transition",
                    "agent_type": "unknown", "session_id": sid,
                    "message": f"Write to {fp}",
                    "metadata": {"file_path": fp},
                })

    return events, interactions


def main():
    try:
        data = json.loads(sys.stdin.read())
        events, interactions = _build_events(data)
        port = int(os.environ.get("CHRONOGRAPH_PORT", str(DEFAULT_PORT)))
        for event in events:
            _post(port, "/api/events", event)
        for interaction in interactions:
            _post(port, "/api/interactions", interaction)
    except Exception:
        pass


if __name__ == "__main__":
    main()
