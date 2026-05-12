# tui-design

Terminal UI and CLI/TUI design craft. Covers the clig.dev CLI contract, output discipline, help text design, error message patterns, TTY detection, exit codes, TUI frameworks, and terminal accessibility.

## When to Use

Load this skill when:
- Designing or reviewing a CLI tool's output formatting, help text, or error messages
- Designing agent or tool output that a human will read in a terminal
- Building or evaluating a full TUI (textual, Ink, Bubble Tea)
- Choosing a TUI framework (textual vs Ink vs Bubble Tea)
- Auditing a CLI for output discipline (stdout/stderr, NO_COLOR, JSON mode, tables)
- Auditing a TUI for render performance (diff-before-render, synchronized output)
- Applying the three-part error message pattern
- Auditing terminal accessibility (NO_COLOR, color depth, screen reader compatibility)

Do **not** load for web UI design (use `web-ui-design`) or API/agent-tool design (use `api-design-craft` or `agentic-interface-design`).

**Boundary note**: when a tool outputs to a terminal that a human reads, that is this skill's concern. When the tool is invoked by a model (its name, description, schema), see `agentic-interface-design`. Both may apply to the same tool.

## Activation

Load automatically when the task involves CLI commands, terminal output, TUI components, help text, error messages, exit codes, or TUI framework selection.

## Skill Contents

| File | Contents |
|------|---------|
| `SKILL.md` | CLI contract overview, output discipline table, three-part error grammar, TTY detection + exit code tables, help-text levels, reference navigation |
| `references/design-fundamentals.md` | Shared cross-cutting design canon — Rams, Norman, Nielsen, Tufte, Bloch, Zhuo, perception thresholds, full canon with one lesson each. **Byte-identical** across all four interface-design skills (intentional; sentinel will flag as redundancy — it is correct). |
| `references/cli-output-and-ux.md` | Full clig.dev distillation, stdout/stderr composability, color discipline in depth, JSON mode, table formatting, progress indicators, quiet/verbose modes, modern CLI exemplars with one lesson each |
| `references/cli-ux-patterns.md` | Help text design (three levels, examples-first rule, jq as exemplar), three-part error message in full (grammar rules, bad/good examples), interactive vs non-interactive handling, `--no-input` flag, exit code table with standard + custom codes |
| `references/tui-frameworks.md` | Model-Update-View architecture (the through-line), Python textual + rich + prompt_toolkit, Node.js Ink, Go Charm ecosystem (Bubble Tea, Lip Gloss, Gum) as the quality exemplar — study Charm's MVU architecture even when building in Python or Node |
| `references/terminal-accessibility.md` | NO_COLOR (the contract and implementation), color depth detection and fallback, never ANSI outside TTY, screen reader considerations, TUI render performance (diff-before-render, DECSET 2026 synchronized output — the Claude Code flicker fix, stream-as-it-arrives, ≤50ms render budget) |
| `references/design-review-checklist.md` | CLI/TUI quality audit checklist (PASS/FAIL/WARN format) — stdout/stderr, color/ANSI, JSON, tables, progress, help text, error messages, interactive/non-interactive, exit codes, TUI render, terminal accessibility |

## Related Skills

- **`web-ui-design`** — sibling hat for web UI design; when a product has both a web UI and a CLI
- **`agentic-interface-design`** — when the CLI is invoked by a model (tool name, description, schema)
- **`api-design-craft`** — API quality lens; when the CLI is a wrapper around an API
