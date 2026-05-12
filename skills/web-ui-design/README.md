# web-ui-design

Web UI and visual interface design craft for React, Next.js, and component-based UIs.

## When to Use

Load this skill when:
- Designing or reviewing web UI components (modals, forms, tables, cards, empty states)
- Choosing between UI layout patterns (modal vs drawer vs inline; table vs card vs list)
- Planning a design system or design-token system
- Evaluating component ergonomics or accessibility
- Deciding a UI framework for a web layer
- Auditing a React/Next.js UI for visual quality, accessibility, or perceived performance
- Applying the WCAG 2.2 AA standard to a web surface
- Making animation timing or perceived-performance decisions for web UI

Do **not** load for terminal/CLI output design (use `tui-design`) or API/agent-tool design (use `api-design-craft` or `agentic-interface-design`).

## Activation

Load automatically when the task involves web UI components, React, Next.js, design tokens, accessibility audits, or component pattern decisions.

## Skill Contents

| File | Contents |
|------|---------|
| `SKILL.md` | Laws of UX, design tokens, WCAG 2.2 numbers, component taste tables, motion timing tables, reference navigation |
| `references/design-fundamentals.md` | Shared cross-cutting design canon — Rams, Norman, Nielsen, Tufte, Bloch, Zhuo, perception thresholds, full canon with one lesson each. **Byte-identical** across all four interface-design skills (intentional; sentinel will flag as redundancy — it is correct). |
| `references/visual-design-fundamentals.md` | Visual hierarchy in depth, CARP, typography (type scale, measure, line height, optical alignment), color systems (5-shade palette, grayscale-first, dark mode token swap, shadow discipline), layout systems |
| `references/component-patterns.md` | Modal/drawer/inline/toast patterns with when-to/when-never, tables vs cards vs lists, form patterns, the five UI states, Linear keyboard-first patterns (command palette, shortcut discoverability) |
| `references/accessibility.md` | WCAG 2.2 AA full requirements, semantic HTML guide, ARIA patterns (disclosure, modal, live regions, tabs), focus management (open/close, focus trap, skip link), accessible primitives (Radix/shadcn pattern), color blindness, prefers-reduced-motion, screen reader guide |
| `references/motion-and-perceived-performance.md` | Animation timing depth, easing functions, GPU-safe properties, RAIL model (Response/Animation/Idle/Load), skeleton vs spinner decision and implementation, optimistic UI patterns, debounce vs throttle, animation-to-mask-latency |
| `references/design-review-checklist.md` | Web UI quality audit checklist (PASS/FAIL/WARN format) — contrast, keyboard nav, focus management, five UI states, design token consistency, motion, component taste, typography, semantic HTML, touch targets |

## Related Skills

- **`tui-design`** — terminal/CLI output and TUI design; the other UI hat
- **`api-design-craft`** — API quality and taste lens; the web UI and its API are both interfaces
- **`agentic-interface-design`** — when the web surface is consumed by an agent or exposes a tool surface
