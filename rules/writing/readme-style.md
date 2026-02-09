## README Writing Style

Technical documentation style for README.md files. Applies the Adaptive Precision philosophy: every sentence must earn its place.

### Core Principle

**Self-contained and precise.** A README succeeds when the reader can understand what the artifact is, what it does, and how to use it — without leaving the document. When a topic requires depth beyond the README's scope, provide minimal inline context so the reader can decide whether to follow the link, then link to the authoritative source rather than inlining a verbose explanation.

### Decision Framework

Match content depth to complexity:

- **Simple/factual** (install command, license) — state it directly, no elaboration
- **Complex/technical** (architecture, non-obvious config) — include reasoning so the reader can apply it correctly
- **Multi-part** (setup steps, API reference) — numbered discrete sections, no connecting prose between them
- **Unclear scope** — state the most literal interpretation with basic prerequisites included

### Mandatory Inclusions

- Include reasoning when: the reader cannot apply the information without understanding the process
- Include prerequisites when: the reader's background knowledge is uncertain
- Include examples when: the concept requires process knowledge to execute correctly

### Mandatory Exclusions

- No social filler — "Welcome to...", "We're excited...", "Feel free to..."
- No hedging — "might", "perhaps", "you could try"
- No encouragement — "Great job!", "You're all set!"
- No satisfaction checks — "Hope this helps!", "Let us know if..."
- No redundant sections — if a section adds nothing the reader needs, omit it

### Emojis and Badges

Utility over cognitive overload:

- Emojis are acceptable when they reduce cognitive load or help the reader visually follow a long sequential or parallel process
- Badges are acceptable under the same criteria — if a badge conveys useful status at a glance (CI, version, coverage), include it
- Avoid decorative emojis and vanity badges that add visual noise without aiding comprehension

### Structure Conventions

- Lead with what the project **is** and **does** — one or two sentences maximum
- Follow with what the reader needs to **use** it (install, configure, run)
- End with what the reader needs to **contribute** or **understand** the internals (only if applicable)
- Omit sections that have no content — an empty "Contributing" section is worse than none
- Use bullet points and numbered lists for scannable content
- Use code blocks for anything the reader will copy-paste

### Scaling Long READMEs

- Add a **TL;DR** + **table of contents** when the document exceeds 4-5 sections
- Split into companion documents (`ARCHITECTURE.md`, `CONTRIBUTING.md`) and link from the main README when depth exceeds entry-point scope

### Structural Integrity

Cross-reference and structural conventions for README.md files that serve as project catalogs or entry points:

- Every filesystem path referenced in a README must point to an existing file or directory
- Catalog READMEs (listing skills, agents, commands, rules) must include every artifact that exists on the filesystem — no phantom entries, no missing entries
- Names in documentation must match actual filenames (hyphens vs. underscores, capitalization)
- Counts stated in prose ("Seven agents") must match the actual number of items listed
- When a README includes a structure tree, it must reflect the current filesystem state
- Cross-references between documentation files must resolve (e.g., links to other READMEs, anchors)

### Naming Consistency

- Use the exact filename (minus extension) when referencing artifacts in documentation
- Prefer the filesystem convention (kebab-case for this project) consistently
- If an artifact was renamed, update all documentation references in the same change

### Writing Quality

- Imperative mood for instructions ("Install the package", not "You should install the package")
- Active voice — "The server handles requests" not "Requests are handled by the server"
- Specific over generic — "Requires Python 3.11+" not "Requires a recent Python version"
- One idea per sentence — break compound explanations into discrete statements
- Consistent terminology — pick one term for each concept and use it everywhere

### Termination Criteria

A README section is complete when the reader has:

1. A direct answer to what they came for
2. The minimum process knowledge to execute correctly, plus enough surrounding context to understand *why* — which may exceed the bare minimum when the topic demands it

If both conditions are met, stop writing. Additional content dilutes signal.
