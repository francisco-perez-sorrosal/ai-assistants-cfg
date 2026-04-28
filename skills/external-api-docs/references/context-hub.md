# context-hub Provider Reference

context-hub (`chub`) is a curated registry of ~600+ LLM-optimized API documentation packages by Andrew Ng's team. It is the default provider for the [external-api-docs](../SKILL.md) skill.

## Installation

```bash
npm install -g @aisuite/chub
```

Or use without global install via `npx`:

```bash
npx -y @aisuite/chub search "stripe"
```

**Prerequisite:** Node.js 18+.

## Configuration

Config file: `~/.chub/config.yaml` (optional -- sensible defaults without it).

```yaml
sources:
  - name: community
    url: https://cdn.aichub.org/v1       # Default public CDN
  - name: internal
    path: /path/to/local/docs            # Optional: private/team docs

source: "official,maintainer,community"  # Trust policy (filter by content source)
refresh_interval: 21600                  # Cache TTL in seconds (default: 6 hours)
output_dir: .context                     # Default output directory for -o flag
```

### Multi-Source Architecture

context-hub merges entries from multiple sources at query time. Add private documentation alongside the public registry:

1. Build private docs: `chub build /path/to/your/content/`
2. Add as a local source in `~/.chub/config.yaml`
3. Both public and private entries appear in search results

Author-prefixed IDs (`author/name`) prevent namespace collisions across sources.

## Telemetry and Feedback Controls

context-hub has two separate opt-out mechanisms:

- **`CHUB_TELEMETRY`** — passive usage analytics (PostHog). Disabled in all Praxion integrations.
- **`CHUB_FEEDBACK`** — enables the explicit `chub feedback` command for rating docs. Left **enabled** so agents can give feedback that improves doc quality for everyone.

**Inspect current state** — the canonical runtime check (introduced in 0.1.4):

```bash
chub feedback --status
```

Prints: feedback enabled/disabled, telemetry enabled/disabled, client ID, endpoint, and the valid feedback labels. Run this whenever you need to confirm the wiring without guessing from env vars.

**Per-command** (recommended in all skill examples):

```bash
CHUB_TELEMETRY=0 CHUB_FEEDBACK=1 chub <command>
```

**Persistent via config** (`~/.chub/config.yaml`):

```yaml
telemetry: false
feedback: true
```

**Environment variables** (shell profile):

```bash
export CHUB_TELEMETRY=0
export CHUB_FEEDBACK=1
```

## CLI Reference

### Search

```bash
chub search "<query>" [--json] [--source official,maintainer]
```

Returns matching docs and skills ranked by BM25 + lexical scoring. Use `--json` for machine-readable output. Use `--source` to filter by trust tier.

### Get

```bash
chub get <author/entry-id> [--lang <language>] [--version <version>] [--file <paths>] [--full] [-o <output>] [--json]
```

| Flag | Purpose |
|------|---------|
| `--lang <language>` | Language-specific version (e.g., `python`, `javascript`) |
| `--version <version>` | Pin to a specific doc version (e.g., `19.1.0`); defaults to the recommended version |
| `--file <paths>` | Fetch one or more specific files (comma-separated paths) without the full doc |
| `--full` | Fetch all reference files (use sparingly -- large token cost) |
| `-o <path>` | Write to file or directory instead of stdout |
| `--json` | Machine-readable output |

Annotations (if any) auto-append to output. Pair `--version` with the project's actual installed version of the library (read from `pyproject.toml`, `package.json`, etc.) to keep the fetched docs aligned with the code being written -- this couples directly with the API Version Drift Detection protocol in `SKILL.md`.

### List All Entries

`chub` 0.1.4 removed the standalone `list` subcommand. Use `search` with no query to enumerate everything:

```bash
chub search                  # list all entries
chub search --json           # machine-readable
chub search --tags openai    # filter by tag without a query
```

The MCP equivalent (`chub_list`) is still available -- the asymmetry is intentional from upstream as of 0.1.4.

### Annotate

```bash
chub annotate <author/entry-id> "<note>"   # write/overwrite (no annotation history)
chub annotate <author/entry-id> --clear    # remove the annotation for this entry
chub annotate --list                       # list every saved annotation
```

A read mode is also available via the MCP (`chub_annotate({ id })` with no other args returns the existing note). Annotations auto-append to future `chub get` output for the same entry.

### Feedback

```bash
chub feedback <author/entry-id> <up|down> [comment] \
  [--label <label>]... [--type <doc|skill>] [--lang <language>] \
  [--doc-version <version>] [--file <path>] [--agent <name>] \
  [--model <model>] [--status]
```

Rate an entry. Requires `CHUB_FEEDBACK=1` (the default).

| Flag | Purpose |
|------|---------|
| `--label <label>` | Structured label (repeatable -- pass `--label outdated --label wrong-examples` to attach multiple) |
| `--type <doc\|skill>` | Explicit entry type when auto-detection is ambiguous |
| `--lang <language>` | Language variant rated (matches `chub get --lang`) |
| `--doc-version <ver>` | Doc version rated (matches `chub get --version`) |
| `--file <path>` | Specific file rated (e.g., `references/streaming.md`) |
| `--agent <name>` | AI coding tool name -- helps maintainers see which agents send which signals |
| `--model <model>` | LLM model name -- same rationale as `--agent` |
| `--status` | Print runtime feedback/telemetry state (does not send feedback) |

Available labels: `accurate`, `well-structured`, `helpful`, `good-examples`, `outdated`, `inaccurate`, `incomplete`, `wrong-examples`, `wrong-version`, `poorly-structured`. The authoritative list is whatever `chub feedback --status` prints.

### Cache Management

```bash
chub update                # Refresh the cached registry index
chub update --force        # Re-download even if the cache is fresh
chub update --full         # Download the full bundle for offline use
chub cache status          # Show cache information
chub cache clear           # Clear cached data
```

## Content Format

context-hub entries follow the [Agent Skills specification](https://agentskills.io/specification):

- **DOC.md** -- API documentation entries. Versioned per-language (`python/1.52.0/DOC.md`). Can include reference files.
- **SKILL.md** -- Behavioral skill entries. Flat, no language/version nesting.

Both use YAML frontmatter with `name`, `description`, and `metadata` fields.

## Trust Tiers

| Tier | Meaning | Reliability |
|------|---------|-------------|
| `official` | Vendor-authored (e.g., Stripe writes Stripe docs) | Highest |
| `maintainer` | Core team or verified maintainer | High |
| `community` | Community-contributed | Variable |

Filter with `--source official,maintainer` to exclude community-contributed entries when accuracy is critical.

## Limitations

- **No semantic search** -- BM25 + lexical matching only; no embeddings
- **Pre-1.0** -- the CLI surface and content format may change between minor versions; verify command shapes with `chub --help` after upgrades and rerun `chub feedback --status` if rating behavior changes
- **Single annotation per entry** -- overwrites, no history (use `--clear` to delete; the only way to keep prior context is to merge it into the new note before writing)
- **No streaming** -- full content fetched at once
- **No programmatic API** -- CLI (`chub`) and MCP server (`chub-mcp`) only; cannot `import` as a library
- **CLI/MCP surface asymmetry** -- not every CLI command has an MCP twin and vice versa (e.g., `chub list` was removed from the CLI in 0.1.4 but `chub_list` remains an MCP tool); consult the binary you are calling, not the other one
