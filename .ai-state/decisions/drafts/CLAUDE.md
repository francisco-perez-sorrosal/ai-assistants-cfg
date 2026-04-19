# ADR Drafts Directory

Fragment ADRs awaiting promotion to stable `<NNN>-<slug>.md` records.

Files here follow the fragment-naming scheme:

```
<YYYYMMDD-HHMM>-<user>-<branch>-<slug>.md
```

with frontmatter `id: dec-draft-<8-char-hash>` and `status: proposed`.

At merge-to-main, `scripts/finalize_adrs.py` promotes each draft to `.ai-state/decisions/<NNN>-<slug>.md`, rewrites its `id`, updates cross-references, and regenerates `DECISIONS_INDEX.md`.

See `rules/swe/adr-conventions.md` for the full specification.
