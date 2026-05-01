---
name: architectural-fitness-functions
description: >
  Architectural fitness functions: codifying ArchUnit-style invariants in Python
  with import-linter (import-graph contracts) and pytest (everything else).
  Covers the decision rubric (when to use which), the citation contract (every rule
  cites an ADR or CLAUDE.md principle in its docstring or description= field), and
  the waiver pattern. Use when authoring fitness rules, deciding whether an invariant
  belongs as an import-linter contract or pytest assertion, choosing between forbidden
  / layered / independence contract types, debugging the meta-citation rule
  (fitness/tests/test_meta_citation.py), or authoring a fitness waiver.
allowed-tools: [Read, Grep, Bash, Write, Edit]
compatibility: Claude Code
---

# Architectural Fitness Functions

Fitness functions make architectural invariants executable. Each rule is a
runnable check that fails loudly when a structural constraint is violated.

**Satellite files** (loaded on-demand):

- [`references/import-linter-recipes.md`](references/import-linter-recipes.md) — authoring import-linter contracts (forbidden, layered, independence patterns, granularity guidance, common pitfalls)

## 1. When to Use This Skill

- Authoring a new architectural invariant (import boundary, layer rule, or convention check)
- Choosing between import-linter and pytest for a given invariant
- Debugging the meta-citation rule (`fitness/tests/test_meta_citation.py`)
- Authoring or reviewing a fitness waiver

## 2. Decision Rubric

```
Is the invariant about which Python module imports which?
├── YES → import-linter contract (in fitness/import-linter.cfg)
└── NO  → pytest test (in fitness/tests/)
```

Common cases:

| Invariant | Tool |
|-----------|------|
| "Layer X must not import from layer Y" | import-linter (`layers` contract) |
| "Module X must never import from module Y" | import-linter (`forbidden` contract) |
| "Modules A and B must not import each other" | import-linter (`independence` contract) |
| "All public functions in module X have docstrings" | pytest (AST-based assertion) |
| "All YAML frontmatter has required field Z" | pytest (file-parsing assertion) |
| "No file in directory D has more than N lines" | pytest (filesystem assertion) |
| "Every fitness rule has a citation" | pytest (the meta-citation rule itself) |

## 3. Citation Contract

Every fitness rule — whether an import-linter contract or a pytest test — **must**
cite its architectural justification. This makes each rule self-documenting and
enables the meta-citation rule to enforce coverage automatically.

**Accepted citation forms:**

- An ADR id matching the pattern `dec-\d{3,}` (preferred when the invariant has a specific decision record)
- A CLAUDE.md principle matching `CLAUDE\.md§[A-Z][A-Za-z ]+` (preferred when the invariant follows from a foundational principle rather than a specific decision)

**Where the citation lives:**

| Rule type | Citation location |
|-----------|-------------------|
| pytest test module | Module docstring (first line is sufficient) |
| import-linter contract | `description=` field of the contract stanza |

**The meta-citation rule** (`fitness/tests/test_meta_citation.py`) scans both
surfaces with the regex `dec-\d{3,}|CLAUDE\.md§[A-Z][A-Za-z ]+`. Any uncited
rule causes the suite to FAIL.

Write the citation **before** the rule logic — it forces upfront justification and
prevents the meta-citation rule from catching you by surprise.

## 4. Waiver Pattern

When an invariant must be temporarily violated (e.g., during a migration), annotate
the offending line with a waiver comment:

```python
import some_forbidden_module  # fitness-waiver: dec-NNN migration in progress
```

A valid waiver requires **both**:
1. A citation anchor matching the citation regex (`dec-\d{3,}` or `CLAUDE\.md§...`)
2. A non-empty reason following the anchor

The meta-citation rule scans waivers and FAILs uncited or reason-less ones.

Waivers are intentionally **distributed** — they live at the point of violation,
not in a centralized `waivers.toml`. This ensures each waiver is reviewed alongside
the code it waives, and waivers surface immediately in code review diffs.

## 5. Authoring Workflow

1. **Pick the location** per the decision rubric (import-linter contract vs. pytest test).
2. **Write the citation first** — in the `description=` field or module docstring —
   before writing the rule logic. This forces upfront justification.
3. **Write the rule** — see [`references/import-linter-recipes.md`](references/import-linter-recipes.md)
   for import-linter contract patterns.
4. **Run the suite**:
   ```bash
   uv run pytest fitness/tests/           # behavior and meta-citation checks
   uv run import-linter --config fitness/import-linter.cfg  # import-graph contracts
   ```
   Both must be GREEN before the rule is considered done.
5. The meta-citation rule self-polices docstring/description coverage — if you forgot
   the citation, the suite FAILs noisily before any merge.

## 6. References

| Reference | When to consult |
|-----------|-----------------|
| [`references/import-linter-recipes.md`](references/import-linter-recipes.md) | Authoring a new import-linter contract (forbidden, layered, independence patterns) |
