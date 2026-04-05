"""Stop hook: block session end when significant work was done without remember().

Scans the transcript for Write/Edit/Agent tool calls and for remember()
calls. If the session did substantial work but never persisted learnings
to memory, blocks the stop (exit 2) with a stderr message prompting the
agent to call remember().

Synchronous hook (async: false). Uses exit 2 + stderr for blocking.
On second attempt (stop_hook_active), re-scans the transcript — only
passes through if remember() was actually called or on the second block
to prevent infinite loops.
"""

from __future__ import annotations

import json
import sys

# Thresholds — tune these based on experience
MIN_EDITS_FOR_SIGNIFICANT = 3
REMEMBER_TOOL_SUBSTRING = "remember"
SIGNIFICANT_TOOLS = frozenset({"Write", "Edit"})
DELEGATION_TOOLS = frozenset({"Agent"})


def _scan_transcript(transcript_path: str) -> tuple[int, int, bool]:
    """Scan transcript for work indicators.

    Returns (edit_count, remember_count, spawned_agents).
    """
    edit_count = 0
    remember_count = 0
    spawned_agents = False

    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    turn = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if turn.get("type") != "assistant":
                    continue

                message = turn.get("message", {})
                content = message.get("content", [])
                if not isinstance(content, list):
                    continue

                for block in content:
                    if block.get("type") != "tool_use":
                        continue

                    name = block.get("name", "")

                    if name in SIGNIFICANT_TOOLS:
                        edit_count += 1
                    elif name in DELEGATION_TOOLS:
                        spawned_agents = True
                    elif REMEMBER_TOOL_SUBSTRING in name.lower():
                        remember_count += 1
    except OSError:
        pass

    return edit_count, remember_count, spawned_agents


def main() -> None:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return

    is_retry = payload.get("stop_hook_active", False)

    transcript_path = payload.get("transcript_path")
    if not transcript_path:
        return

    edit_count, remember_count, spawned_agents = _scan_transcript(transcript_path)

    # If remember() was called, always pass through
    if remember_count > 0:
        return

    significant_work = edit_count >= MIN_EDITS_FOR_SIGNIFICANT or spawned_agents
    if not significant_work:
        return

    # Second attempt and still no remember() — let through to avoid infinite loop
    if is_retry:
        return

    detail = []
    if edit_count > 0:
        detail.append(f"{edit_count} file edits")
    if spawned_agents:
        detail.append("agent delegation")
    work_summary = ", ".join(detail)

    message = (
        f"[memory-gate] You did significant work ({work_summary}) but never "
        f"called remember(). You MUST call the mcp__plugin_i-am_memory__remember "
        f"tool now before stopping. Examples of what to remember:\n"
        f"- Gotchas or non-obvious behaviors you discovered\n"
        f"- Patterns that worked well and should be reused\n"
        f"- User corrections or preferences expressed this session\n"
        f"- Conventions or constraints not documented elsewhere\n"
        f"- Architectural insights or trade-off rationales\n\n"
        f'Call: mcp__plugin_i-am_memory__remember with category="learnings", '
        f"a descriptive key, the insight as value, relevant tags, "
        f"importance (3-8), a one-line summary, and type "
        f"(decision/gotcha/pattern/convention/preference/correction/insight)."
    )
    print(
        json.dumps({"decision": "block", "reason": message}),
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # fail-open ��� never crash the session
