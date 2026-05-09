---
paths:
  - "streamlit_app/**"
  - "**/*.html"
  - "**/doc_manifest.yaml"
  - "**/components/**.py"
  - "**/components/**.j2"
  - "**/components/**.jinja"
  - "**/components/**.html"
---

## HTML Output Conventions

Praxion uses HTML as a **presentation veneer over Markdown source**, never as a replacement. Markdown stays the canonical source of truth for both human and agent reading; HTML enhances the human reading experience by adding visual structure, hides dense content behind anchored links to MD sections, and is assembled by the per-project Streamlit dashboard. This rule applies when authoring or modifying anything in the rendering layer — Streamlit pages, component library files, doc manifests, and committed `.html` artifacts.

### The Architectural Pattern

```
MD = source of truth + agent surface  (always; never duplicated)
   ↑
   │ HTML wraps, never copies; links into MD section anchors
   ↓
HTML = human-only presentation veneer  (rendered, not authored)
   ↑
   │ Streamlit assembles; reads MD/JSON/YAML/SVG live
   ↓
Streamlit = single per-project entry point  (single-source aggregator)
```

**Three invariants:**

1. **Markdown is canonical.** Every fact lives in exactly one place — an MD file, a YAML manifest, an SVG render, or an ADR. HTML and Streamlit are *views* of those facts, never owners.
2. **No content duplication.** HTML never copies MD prose. It links to MD section anchors, embeds rendered SVGs, and (when a section needs to be inlined) reads the MD at view-time via Streamlit (`st.markdown(open(path).read())`).
3. **Agents always read MD.** The HTML layer never enters agent context. Agent token budgets are unaffected by HTML rendering.

### Hybrid Render Boundary

Two render modes coexist; pick by audience and lifetime:

| Render mode | When | Where | Persistence |
|---|---|---|---|
| **Streamlit-rendered** (default) | Ephemeral pipeline artifacts, in-flight project state, per-project navigation | `streamlit_app/components/` reads MD/JSON/YAML on session start, emits HTML to embed via `st.components.v1.html` or Streamlit-native widgets | None on disk; rendered live; closes when Streamlit stops |
| **Pre-rendered** (committed) | Share-out artifacts intended to be linked from PRs, emails, slack, or external sites | Pre-commit hook generates `<file>.html` alongside the MD source; both committed | On disk in git; opt-in via frontmatter `share_out: true` |

**Defaults:**

- `IMPLEMENTATION_PLAN.md`, `SYSTEMS_PLAN.md`, `VERIFICATION_REPORT.md`, `IDEA_PROPOSAL.md`, `WIP.md`, `TEST_RESULTS.md` → **Streamlit-rendered only.** No `.html` companion on disk; the dashboard renders them live.
- `docs/architecture.md`, `.ai-state/DESIGN.md`, `docs/concepts.md`, `docs/aac-dac.md` → **Streamlit-rendered by default.** Add `share_out: true` to the frontmatter when a stable shareable link is needed (e.g., a public docs deploy or a one-off explainer for stakeholders).
- `README.md`, `CLAUDE.md`, ADRs, rules, skills → **MD only, no HTML at all.** These are agent-first or GitHub-first surfaces; HTML never enters their picture.

### Component Library

HTML rendering is **not hand-authored per artifact**. A small library of reusable, content-typed renderers lives at `streamlit_app/components/` (Python or Jinja templates). Streamlit selects the renderer by file type + Diátaxis frontmatter.

**Initial component set:**

| Component | Consumes | Renders |
|---|---|---|
| `plan_view` | `IMPLEMENTATION_PLAN.md` + `WIP.md` | Step cards with progress, blockers, acceptance criteria expandable |
| `adr_card` | `<NNN>-*.md` ADR | Frontmatter as header chip; body collapsed; supersedes/re-affirms graph |
| `verification_report` | `VERIFICATION_REPORT.md` | Color-coded findings (PASS / WARN / FAIL); contract-violation tags as filters |
| `architecture_explorer` | `DESIGN.md` + `architecture.md` + diagrams | Three-pane: Diátaxis-explanation / code-verified-reference / live SVG viewport |
| `traceability_matrix` | `traceability.yml` + spec | Sortable table; REQ → test → impl click-through |
| `idea_grid` | `IDEA_PROPOSAL.md` + `IDEA_LEDGER_*.md` | Side-by-side proposal cards |
| `metrics_view` | `METRICS_REPORT_*.json` | Existing metrics page (already in `streamlit_app/`) |

**Adding a new component:** create a new module under `streamlit_app/components/<name>/` exporting a `render(source_paths, ...)` callable. Register it in `streamlit_app/components/__init__.py`'s renderer map keyed by content type. Document its `Consumes:` and `Renders:` rows in `streamlit_app/components/README.md`.

### Diátaxis-Typed Shells

When rendering an MD file, the renderer chooses a shell based on the `diataxis:` frontmatter:

| `diataxis:` value | Shell template | Visual emphasis |
|---|---|---|
| `tutorial` | progress-through-steps wrapper; "what you'll have built when done" header | sequential numbered cards, prereq sidebar |
| `how-to` | numbered checklist + copy-paste blocks + verification commands | terse, scan-friendly, command emphasis |
| `reference` | sortable tables, anchored navigation, search bar | dense data, table-of-contents fixed sidebar |
| `explanation` | wide-text + illustration-heavy + "why this matters" sidebar | prose flow, embedded diagrams, no commands |
| `concepts` | glossary + decision rationale + relationship graph | conceptual map, cross-references prominent |

The MD body is rendered into the shell's content slot. **Same source, different cognitive ergonomics.**

### No JavaScript in HTML

Committed `.html` files (share-out renders) are **declarative HTML + CSS + SVG only.** No `<script>` tags. No client-side fetch. No interactive widgets embedded in the HTML.

**Interactivity lives in Streamlit:**

| Interaction | Mechanism |
|---|---|
| Filter / search | `st.text_input`, `st.selectbox`, `st.multiselect` |
| Sort / re-order | `st.dataframe` with column sort |
| Export / copy | `st.download_button` for files; `st.code` with copy icon for snippets |
| "Copy as prompt" pattern | `st.button` that writes to `streamlit.session_state` and displays via `st.code(language="text")` |
| Diff annotations / highlight | `st.markdown` with HTML allowed (`unsafe_allow_html=True`) and a strict allowlist |

**Why:** two interaction layers (HTML JS + Streamlit widgets) double maintenance and conflict over event handling. Pushing all interactivity to Streamlit unifies the model.

### MD Inlining via Streamlit

When a renderer needs to embed MD content inline (e.g., a how-to guide's commands inside a tutorial wrapper):

```python
# components/how_to/render.py
import streamlit as st
from pathlib import Path

def render(md_path: Path):
    raw = md_path.read_text()
    frontmatter, body = split_frontmatter(raw)
    st.markdown(body)  # MD body rendered live
```

**Never:**

- Pre-bake MD content into the HTML at build time (creates a stale derivative; defeats the single-source rule).
- Fetch MD via client-side JavaScript at render time (fragile, breaks offline, security headaches).
- Copy MD prose into the renderer's source code (dual-maintenance burden).

The only allowed flow is: `MD on disk → Streamlit reads at view-time → renders into shell → user sees`.

### `doc_manifest.yaml` — the Entry-Point Spine

Each project ships a `.ai-state/doc_manifest.yaml` listing every doc surface with type, renderer, location, and relationships. The Streamlit dashboard reads it on session start to build navigation. Schema lives in [`skills/doc-management/references/doc-manifest-schema.md`](../../skills/doc-management/references/doc-manifest-schema.md) (when authored).

The manifest is **generated**, not hand-maintained — `scripts/build_doc_manifest.py` walks `docs/`, `.ai-state/`, `.ai-work/<active-slug>/` and emits the YAML. Sentinel check `EC07-doc-manifest-fresh` validates it stays in sync with the filesystem.

### Sharability and File Layout

For pre-rendered share-out artifacts:

- `<file>.html` lives alongside `<file>.md` (same directory, parallel name).
- Pre-commit hook generates the HTML from MD source.
- `.gitattributes` marks `*.html` files as generated (so GitHub diff view collapses them by default).
- The MD always remains the canonical edit target; humans never edit the `.html` directly.

For Streamlit-rendered artifacts:

- The Streamlit dashboard is launched via `/dashboard` (delegates to `praxion-dashboard`).
- The same MD source feeds both human-via-Streamlit and agent-direct-read.
- A "share" button in the Streamlit page can export a snapshot HTML for one-time send-out (e.g., `streamlit_app/components/<name>/render.py` exposes `to_static_html()` for ad-hoc export).

### Authorship Boundary (Who Writes HTML?)

| Author | What they author |
|---|---|
| Skill / agent / convention authors | **MD only.** Never HTML. Frontmatter declares `diataxis:` and (optionally) `share_out: true`. |
| `streamlit_app/components/` maintainers | Renderer code (Python + Jinja). Components are reusable; one renderer serves N artifacts of the same type. |
| Pre-render hook (auto-generated) | `<file>.html` for `share_out: true` files. Never hand-edit the output. |
| User / dashboard user | Reads only. May export ad-hoc snapshots via Streamlit "share" buttons. |

This is the same single-author-per-surface discipline already enforced for MD docs (per `rules/writing/readme-style.md`) — extended to the HTML layer.

### Integration with `diagram-conventions.md`

The diagram source/render separation already established in [`diagram-conventions.md`](diagram-conventions.md) composes cleanly: SVG renders are embedded as `<img>` tags in HTML the same way they're embedded in Markdown. No additional mechanism needed. When a renderer (e.g., `architecture_explorer`) needs to embed an SVG, it reads the same `<doc-tree>/diagrams/<name>/rendered/<name>.svg` path the MD source references.

### Self-test Before Committing HTML-Layer Changes

- Did I author MD source first, with HTML rendering as a derived view?
- Did I check that no MD content is duplicated into HTML or Python source?
- Did I select the appropriate renderer from `streamlit_app/components/` rather than hand-authoring a one-off HTML page?
- For interactivity, did I use Streamlit widgets rather than HTML+JS?
- For MD content embedding, did I use `st.markdown(open(path).read())` (view-time read) rather than pre-baking?
- Did I add the new doc surface to `.ai-state/doc_manifest.yaml` (or trigger the generator that does)?

### Migration Clause (Existing Streamlit Pages)

Streamlit pages authored before this convention took effect (e.g., the existing metrics page) **stay in place**. Migration to the component-library structure happens opportunistically when a page is touched for any other reason. Sentinel check `EC07b-streamlit-page-uses-components` (when implemented) flags pages that bypass the renderer registry, but does not block — it advises.

### Anchored Cross-Reference

The full rationale, sub-phases (HTML-A through HTML-F), and migration sequencing live in `.ai-state/decisions/drafts/` (the locked HTML strategy will get its own ADR when this rule is finalized at merge-to-main).
