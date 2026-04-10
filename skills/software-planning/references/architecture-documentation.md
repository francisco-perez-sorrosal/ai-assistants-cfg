# Architecture Documentation

Living document methodology for `.ai-state/ARCHITECTURE.md`. Back to [SKILL.md](../SKILL.md).

## Purpose

The software-planning skill provides generic architecture *planning* knowledge (pipeline, decomposition, coordination). Each project captures its specific architectural *state* in `.ai-state/ARCHITECTURE.md` -- a living document maintained by the agent pipeline.

**Software-planning skill** = how to plan and execute architectural work
**ARCHITECTURE.md** = WHAT this system IS (components, data flow, interfaces, constraints)

## Document Lifecycle

### Creation

The **systems-architect** creates the document from the template (`assets/ARCHITECTURE_TEMPLATE.md`) during Phase 3.8 when the pipeline is Standard or Full tier. It fills in:
- Section 1 (Overview): quick-facts table and summary
- Section 2 (System Context): L0 boundary diagram and external actors
- Section 3 (Components): skeleton with known components
- Section 5 (Data Flow): key scenario flows
- Section 7 (Constraints): known limitations and quality attributes
- Section 8 (Decisions): cross-references to architecture-related ADRs

Sections 4 (Interfaces) and 6 (Dependencies) are left with template guidance for the implementer to fill as-built.

Skip creation for trivially simple projects (single module, no external dependencies).

### Updates

The **implementer** is the most frequent updater. After completing any step annotated with `[Architecture]` or that creates/modifies structural files, it updates the corresponding section:

| Change Type | Sections Updated |
|-------------|-----------------|
| New module/package created | 3 (Components: add to table and L1 diagram) |
| Interface/API changes | 4 (Interfaces: update contract table) |
| Data model changes | 5 (Data Flow: update flow descriptions) |
| New dependency added/removed | 6 (Dependencies: update table) |
| ADR created | 8 (Decisions: add cross-reference row) |

If `.ai-state/ARCHITECTURE.md` does not exist, the implementer skips architecture updates -- the systems-architect creates it.

### Validation

The **verifier** cross-checks the document against actual code during Phase 4.8:
- Component names (Section 3) match actual module/directory names on disk
- File paths in the component table exist on disk
- ADR IDs in Section 8 correspond to actual files in `.ai-state/decisions/`
- Dependencies in Section 6 match actual project dependencies
- Component count is roughly consistent with actual module count

A stale architecture doc is a WARN, not a FAIL -- it's advisory, not a gate.

### Auditing

The **sentinel** audits with four checks:
- **AC01**: Architecture doc exists when project has 3+ interacting components
- **AC02**: Component names in ARCHITECTURE.md match actual modules
- **AC03**: File paths in ARCHITECTURE.md resolve to existing files
- **AC04**: ADR cross-references in Section 8 are valid

## Section Ownership Model

Each agent owns specific sections to prevent conflicts:

| Section | Owner(s) | Update Trigger |
|---------|----------|----------------|
| 1. Overview | systems-architect | Architecture changes |
| 2. System Context | systems-architect | New external dependencies |
| 3. Components | systems-architect (skeleton), implementer (as-built) | New module/package, major refactoring |
| 4. Interfaces | systems-architect (design), implementer (as-built) | Interface changes |
| 5. Data Flow | systems-architect | Data model changes, new flows |
| 6. Dependencies | systems-architect, implementer | Dependency additions/removals |
| 7. Constraints | systems-architect | Constraint discovery |
| 8. Decisions | systems-architect | ADR creation |

Natural pipeline sequencing prevents concurrent edits: architect writes first (Phase 3), implementer updates later (Execution), verifier validates last.

## Staleness Mitigation

Four layers of defense:

1. **Main agent awareness** -- when modifying structural files in Direct/Lightweight tier (no pipeline), the main agent checks for `.ai-state/ARCHITECTURE.md` and updates affected sections. This document's Coordinator Awareness section provides the guidance
2. **Implementer post-step** -- in Standard/Full pipelines, updates doc when structural files change (proactive, step 7.6)
3. **Verifier Phase 4.8** -- cross-checks doc vs actual code structure after implementation (reactive, per-pipeline)
4. **Sentinel audit** -- checks existence and consistency independently (reactive, periodic). Finding routing:

| Check | Finding | Recommended Owner | Fix Action |
|-------|---------|-------------------|------------|
| AC01 | 3+ components, no architecture doc | systems-architect | Create ARCHITECTURE.md from template on next pipeline |
| AC02 | Component names don't match modules | implementer or main agent | Sync Section 3 with actual module names |
| AC03 | File paths in doc don't resolve | implementer or main agent | Update stale file references |
| AC04 | ADR reference in Section 8 invalid | systems-architect | Fix or remove broken ADR reference |

The sentinel detects but never fixes (read-only). Its report routes findings to the appropriate agent or the main agent for next-session pickup.

## Relationship to ADRs

ADRs document *why* an architectural decision was made. The architecture doc documents *what* the current architecture is. They complement each other:

- The architecture doc references ADR IDs in Section 8 for rationale
- Architecture-related ADRs include `ARCHITECTURE.md` in `affected_files`
- Never duplicate ADR rationale in the architecture doc -- just link

## Relationship to SYSTEM_DEPLOYMENT.md

ARCHITECTURE.md and SYSTEM_DEPLOYMENT.md are complementary, not overlapping:

- **ARCHITECTURE.md** defines the building blocks -- components, interfaces, data flow, constraints
- **SYSTEM_DEPLOYMENT.md** describes how those blocks land on infrastructure -- containers, ports, config, runbook

Architecture is upstream; deployment is downstream. The building blocks defined in ARCHITECTURE.md are what SYSTEM_DEPLOYMENT.md deploys.

**Cross-reference pattern** (never duplicate):
- ARCHITECTURE.md Section 2 (System Context) references SYSTEM_DEPLOYMENT.md for deployment topology
- ARCHITECTURE.md Section 6 (Dependencies) references SYSTEM_DEPLOYMENT.md Section 6 for failure analysis
- SYSTEM_DEPLOYMENT.md Section 2 references ARCHITECTURE.md for full architecture context

**Boundary rule**: if the content describes *what the system is* (structure, behavior, contracts), it belongs in ARCHITECTURE.md. If it describes *how the system runs* (containers, ports, health checks, scaling, runbook), it belongs in SYSTEM_DEPLOYMENT.md.

## Coordinator Awareness

For Direct/Lightweight tier work (no pipeline agents), the main agent should be aware of `.ai-state/ARCHITECTURE.md`:

- **Discovery**: Target projects should add a one-line mention to their CLAUDE.md: "Architecture documentation at `.ai-state/ARCHITECTURE.md`"
- **When to read**: Before making structural decisions (adding modules, changing interfaces, introducing dependencies)
- **When to update**: After structural changes -- new modules, interface changes, dependency additions/removals
- **When NOT to update**: Bug fixes, refactoring within existing modules, test changes, documentation updates

The systems-architect adds the CLAUDE.md mention when creating the initial ARCHITECTURE.md. No hook injection or path-scoped rule is needed -- this is on-demand, progressive disclosure.

## Diagram Conventions

Follow the project's Mermaid diagram conventions (see `rules/writing/diagram-conventions.md`):

- **10-12 nodes maximum** per diagram
- **L0/L1/L2 decomposition**: L0 for system context, L1 for components, L2 for internals (only when needed)
- **Standard shapes**: rectangles for components, `[(Database)]` for storage, `([Queue])` for messaging
- **Solid arrows** (`-->`) for direct dependencies, **dotted** (`-.->`) for async/event-based
- **Subgraphs** for logical boundaries (layers, bounded contexts)
- **Labels over IDs**: `App[Web App]` not bare `App`

## Bootstrap for Existing Projects

For projects that already have code but no architecture doc:

1. The sentinel's AC01 check flags the gap (3+ interacting components, no ARCHITECTURE.md)
2. The systems-architect creates the doc when next invoked for a Standard/Full pipeline
3. Read existing code structure, imports, and config to populate components, interfaces, and dependencies
4. Read existing ADRs in `.ai-state/decisions/` to populate Section 8
