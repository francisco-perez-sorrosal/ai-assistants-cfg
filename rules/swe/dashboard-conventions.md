---
paths:
  - "streamlit_app/**/*.py"
  - "streamlit_app/**/*.toml"
  - "scripts/praxion-dashboard"
---

## Dashboard Conventions

Declarative constraints for any agent editing files under `streamlit_app/` or `scripts/praxion-dashboard`. These encode non-obvious invariants that the dashboard's correctness depends on. For how to build Streamlit pages, use the [Streamlit docs](https://docs.streamlit.io/) directly.

### 1. Pure Data Layer

Modules under `streamlit_app/data/` MUST be pure functions. They MUST NOT import or call any Streamlit rendering primitive (`st.write`, `st.markdown`, `st.dataframe`, `st.metric`, etc.). The only Streamlit symbol permitted in `data/` modules is `st.cache_data` from `streamlit`. No global mutable state.

Rationale: purity makes the data layer unit-testable with plain `pytest` and no Streamlit runtime. Any rendering import in `data/` is a convention violation, not a style preference.

### 2. mtime-Keyed Caching

Every `@st.cache_data` decorator on a data-layer function MUST declare an `mtime: float` parameter as its first non-`path` argument. Callers pass `data.cache.mtime_of(path)` as the value. The cache SHOULD use `ttl=None` for path-keyed parser wrappers; `mtime` is the file-content invalidation key.

```python
# Correct — mtime is part of the cache hash; file change → new hash → cache miss → fresh read
@st.cache_data(ttl=None)
def cached_read_file(path: Path, mtime: float) -> Optional[str]: ...

# WRONG — leading underscore tells Streamlit to EXCLUDE the parameter from the cache hash;
# the cache will silently serve stale data forever (until ttl expires or clear_all() is called).
# This is the most consequential gotcha in the data layer — the underscore convention is for
# unhashable args (database connections, file handles), not for invalidation keys.
@st.cache_data(ttl=None)
def cached_read_file(path: Path, _mtime: float) -> Optional[str]: ...

# Wrong — missing mtime; relies on TTL alone, which causes stale reads up to ttl seconds.
@st.cache_data
def read_file(path: Path) -> Optional[str]: ...
```

Rationale: Streamlit's `@st.cache_data` excludes underscore-prefixed parameters from the cache key hash. To make `mtime` actually invalidate, the parameter name must NOT start with an underscore — file change → new mtime → new hash → cache miss → fresh read. TTL-only caching causes the dashboard to serve stale data for up to `ttl` seconds after a file changes; mtime-keyed hashing is precise and immediate.

### 3. Fragment-Based Auto-Refresh Only

Live-data refresh MUST use `@st.fragment(run_every=<seconds>)`. Adding `streamlit-autorefresh` or any other package that triggers full-page reruns is prohibited.

```python
# Correct
@st.fragment(run_every=config.POLL_SECONDS)
def _render_workshop(slug_dir: Path) -> None: ...

# Wrong — full-page rerun destroys scroll position and causes flicker
st_autorefresh(interval=15000)
```

Rationale: full-page reruns destroy scroll position and cause visible flicker. `@st.fragment` confines reruns to the subtree that needs live data.

### 4. Frontmatter Stripped Before Markdown

When passing Markdown content to `st.markdown`, YAML frontmatter MUST be parsed out first via `data.parsers.parse_frontmatter()`. Frontmatter is presented as a metadata table or popover, never as raw text inside the Markdown body.

```python
# Correct
metadata, body = parse_frontmatter(raw_text)
st.markdown(body)

# Wrong — frontmatter appears verbatim as --- blocks in the rendered page
st.markdown(raw_text)
```

Rationale: ADRs, sentinel reports, idea ledgers, and other artifacts carry YAML frontmatter that is not part of the human-readable body. Rendering it raw produces a broken page with visible `---` delimiters and unescaped YAML fields.

### 5. Empty-State Degradation

Every page module's `render()` MUST handle the case where its source artifact(s) do not exist or are unreadable. Pages MUST NOT raise an exception on missing files; they degrade to `widgets.empty_state(artifact_name, producer_skill_path)`.

```python
# Correct
def render() -> None:
    path = discovery.find_roadmap(config.PROJECT_ROOT)
    if path is None:
        empty_state("ROADMAP.md", "commands/roadmap.md")
        return
    ...

# Wrong — raises FileNotFoundError when ROADMAP.md is absent
def render() -> None:
    text = config.PROJECT_ROOT.joinpath("ROADMAP.md").read_text()
    ...
```

Rationale: transient and sparse projects are first-class. `.ai-work/` directories disappear when a pipeline completes; `.ai-state/` artifacts are absent in freshly onboarded projects. A page that raises on missing files is broken for the common case.

### 6. Single `render()` Entry Per Page

Each module under `streamlit_app/pages/` MUST export exactly one `render() -> None` callable. Modules MUST NOT execute Streamlit calls at import time: no module-level `st.set_page_config`, no module-level `st.write`, no module-level data fetches.

```python
# Correct
def render() -> None:
    st.header("Roadmap")
    ...

# Wrong — st.write executes at import time, breaking app.py composition
st.write("Roadmap")

def render() -> None: ...
```

Rationale: `app.py` uses `st.navigation` and passes page modules as callable references. Import-time rendering executes before `st.set_page_config` runs, breaks page composition, and makes pages un-testable in isolation.
