---
id: dec-draft-ded4fd86
title: Verifier clusters findings by smell-class first, then file-locality within a class
status: proposed
category: architectural
date: 2026-05-14
summary: Verifier Phase 12.5 groups findings into rework rows by (a) smell-class (architecture vs. implementation) and (b) overlapping location file-sets within a class. Findings spanning both classes become two rows; the architect re-clusters during Phase 1 if needed.
tags: [verifier, clustering, rework, smell-class, file-locality]
made_by: agent
agent_type: systems-architect
branch: worktree-verifier-rework-loop
pipeline_tier: standard
affected_files:
  - agents/verifier.md
---

## Context

The verifier emits one `REWORK_MANIFEST.md` row per finding cluster, each cluster spawning one rework worktree. The cluster boundary determines:

- How many worktrees fire per pipeline (one cluster = one worktree = one user-facing fresh-session action).
- Which findings the dispatched agent (per `dec-draft-b3b1abda`, the architect first) sees in its `VERIFIER_FINDINGS.md`.
- The blast radius of the worktree: a tight cluster touches few files; a loose cluster touches many.

The verifier emits findings tagged with smell-class metadata (`[INTERFACE-DESIGN-MISMATCH]`, `[BLOAT]`, `[NON-SURGICAL]`, `[SCOPE-CREEP]`, `[UNSURFACED-ASSUMPTION]`, `[MISSING-OBJECTION]`, `[DEAD-CODE-UNREMOVED]`, severity-only Phase 5 convention findings, etc.) and each finding has a `location` (file path + optional line range).

**Activation:** yes (algorithmic decision, downstream-blast-radius surface, testability concern). Lenses applied: Testability (deterministic rubric), Surgical (small clusters), Future-proof.

## Decision

Hybrid clustering: smell-class first, then file-locality within a class.

### Algorithm (pseudocode)

```
def cluster_findings(findings):
    clusters = []
    # Step 1 — bucket by smell-class
    by_class = {"architecture": [], "implementation": []}
    for finding in findings:
        cls = classify_smell_class(finding.tag)  # see mapping below
        by_class[cls].append(finding)
    # Step 2 — within each class, bucket by overlapping file sets
    for cls, items in by_class.items():
        groups = []
        for finding in items:
            file_set = frozenset(finding.location_files)
            merged = False
            for group in groups:
                if file_set & group.files:  # any overlap
                    group.add(finding)
                    group.files |= file_set
                    merged = True
                    break
            if not merged:
                groups.append(Group(finding, file_set))
        for group in groups:
            clusters.append(Cluster(cls, group.findings))
    return clusters
```

### Smell-class mapping (verifier tag → class)

| Tag | Class |
|---|---|
| `[INTERFACE-DESIGN-MISMATCH]` | architecture |
| `[Architecture:design]` FAIL/WARN | architecture |
| `[Architecture:guide]` FAIL/WARN | implementation (doc-engineer / implementer scope) |
| `[Deployment]` FAIL/WARN | architecture |
| `[Security: <Category>]` FAIL | implementation (unless category indicates a design flaw, then architecture) |
| `[BLOAT]`, `[DEAD-CODE-UNREMOVED]`, `[NON-SURGICAL]`, `[SCOPE-CREEP]` | implementation |
| `[UNSURFACED-ASSUMPTION]`, `[MISSING-OBJECTION]` | implementation (behavioral-contract scope is per-step, not architectural) |
| Phase 5 convention-compliance findings | implementation |
| `[Spec Conformance: ...]` FAIL | implementation |
| Untyped FAIL/WARN | implementation (default) |

The mapping is embedded in the verifier's Phase 12.5 process body. It is reversible — re-classifying a tag is a one-line edit. The architect re-applies its own judgment in Phase 1 of the rework worktree and can re-classify if needed (REQ-RWK-09's routing-through-architect makes this safe).

## Considered Options

### Option 1 — By smell-class only

Every `[INTERFACE-DESIGN-MISMATCH]` becomes one cluster, every `[BLOAT]` another. Pros: simplest. Cons: a cluster could span unrelated files, producing too-broad worktrees.

Rejected.

### Option 2 — By file only

Every finding sharing a file becomes one cluster. Pros: tight file-locality. Cons: bundles architectural and implementation smells into one worktree; the dispatched agent (architect) gets a confused intake.

Rejected.

### Option 3 — By call-graph (transitive)

Build a per-finding call graph; cluster transitively. Pros: theoretically most accurate. Cons: requires static-analysis infrastructure Praxion lacks; deterministic test surface is harder.

Deferred — migration path if/when call-graph tooling lands.

### Option 4 — By `DESIGN.md` component

Resolve `location` files to Architecture components; cluster by component. Pros: aligns with architecture taxonomy. Cons: requires every file to map to a component; mapping is fragile when components are coarse (whole subsystems) or absent for new files.

Deferred — usable as a refinement on Option 5 if `DESIGN.md` is well-populated.

### Option 5 — Hybrid: smell-class then file-locality (chosen)

Pros: smell-class boundary keeps a cluster's intake focused (architect on architecture findings, planner-via-architect on implementation findings); file-locality within a class produces small worktrees with bounded blast radius; deterministic and testable.

Cons: a single root-cause issue surfacing as both architecture and implementation findings produces two clusters → two worktrees → two reworks. The architect Phase 1 can re-merge during analysis if it detects this.

**Chosen.**

## Consequences

**Positive:**

- Deterministic rubric: same finding set produces same cluster set across runs.
- Test surface is bounded: per-class file-overlap clustering is small-set logic, easy to unit-test.
- The smell-class boundary aligns with the routing-through-architect decision (`dec-draft-b3b1abda`) — even though every rework goes through the architect, the manifest's `class` field still informs the user about expected downstream agent involvement.
- Each rework worktree's scope is small (file-locality bounded), which keeps the worktree's blast radius narrow.

**Negative:**

- Multi-class root causes produce multiple worktrees. Acceptable: the architect's Phase 1 re-clustering can identify and consolidate; the manifest's `dedup_against` field can record the relationship on a re-run.

**Mitigation:**

- The architect on Phase 1 sees both worktrees' findings (via the parent's snapshotted `VERIFICATION_REPORT.md` per `dec-draft-d70b274f`) and can recommend consolidating to the user.
- A future enhancement could add a `multi-class` cluster type; the rubric is reversible.

## Open Item

The exact mapping of tags to classes in the table above is the architect's best guess from reading `agents/verifier.md` Phase 3–11. The implementer should validate this against actual verifier outputs during implementation; if a tag is consistently mis-classified, the mapping is a one-line edit in the verifier's Phase 12.5 process body — this ADR does not freeze the mapping, only the algorithm.
