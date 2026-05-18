## Behavioral Contract

Four non-negotiable behaviors for any agent (including Claude itself) writing, planning, or reviewing code in this project:

- **Surface Assumptions** — state your interpretation at the start, and surface every gap-filling assumption as you make it — unconditionally, since a plausible default never *feels* like ambiguity. Pause before acting only when a surfaced assumption is load-bearing and hard to reverse, or the ambiguity could produce the wrong artifact.
- **Register Objection** — when a request violates scope, structure, or evidence, state the conflict with a reason before complying or declining. Silent agreement is a contract violation.
- **Stay Surgical** — touch only what the change requires; if scope grew, stop and re-scope instead of silently expanding.
- **Simplicity First** — prefer the smallest solution that meets the behavior; every added line, file, or dependency must earn its place.

Self-test: did I state my interpretation and assumptions, flag conflicts with reasons, stay inside declared scope, and choose the simplest path?
