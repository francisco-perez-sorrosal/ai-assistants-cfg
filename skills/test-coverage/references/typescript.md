# TypeScript Reference

TypeScript-specific mechanics for the [`test-coverage`](../SKILL.md) skill. Loaded on demand when the active project is detected as TypeScript.

This reference does **not** install Vitest, `@vitest/coverage-v8`, or any other tool. The project owns its coverage dependency. The default config block below is copy-pasteable into a project's `vitest.config.ts`; adoption is the project's decision.

## Target-Discovery Probe Order

Probe these sources in order and stop at the first hit. Each check is a simple filesystem or file-content test — the skill does not execute anything during probing.

1. **`package.json` scripts** — look for a coverage-oriented script (commonly `coverage`, `test:coverage`, `test:cov`, or a script containing `--coverage`). If present, invoke via `npm run <script-name>` (or `yarn`/`pnpm` as detected by lock file). Package scripts almost always pin the correct invocation, including correct paths and reporter flags.
2. **`vitest.config.ts` / `vitest.config.js`** — check for a `coverage` block. If present, invoke `npx vitest run --coverage`. Vitest reads thresholds and reporter config automatically; this is the canonical target for TypeScript projects using Vitest.
3. **`vitest.config.ts` without coverage block** — if Vitest is present (detectable by `"vitest"` in `devDependencies` in `package.json`) but no coverage config block exists, fall back to `npx vitest run --coverage`. This is a best-effort branch — emit a clear message that no coverage config block was found and defaults will apply (no thresholds, V8 provider).
4. **Makefile target** — if a `Makefile` exists with a target named `coverage`, `test-coverage`, or `cov`, invoke via `make <target>`. This is the lowest-precedence branch because it may shell out to a different invocation and the exact behavior is project-specific.

If all four probes fail, return a structured "no target found" result. The appropriate remediation is to add `@vitest/coverage-v8` as a real dependency and adopt the default config block below — not to bootstrap anything from inside the skill.

## Invocation Conventions

- **Invoke through the project's package manager when one is detected.** For projects with `pnpm-lock.yaml`, prefer `pnpm run coverage`. For `yarn.lock`, prefer `yarn coverage`. For `package-lock.json`, prefer `npm run coverage`. Running through the package manager ensures the correct local `node_modules` is active.
- **`vitest run --coverage` is the standard invocation.** The `run` subcommand runs once and exits (no watch mode), which is correct for CI and coverage collection.
- **Stream output to stderr, not stdout.** The calling surface (command, metrics pipeline, verifier) may want stdout reserved for a clean result; Vitest chatter belongs on stderr.
- **Propagate non-zero exits.** If Vitest exits non-zero (test failure, collection error, missing tool), surface the exit code. Callers that want to downgrade failure to a warning wrap the invocation — the skill itself does not swallow failures.
- **Do not mutate project config.** The skill reads `vitest.config.ts` and `package.json` during probing but never writes to them. Config adoption is a user-driven one-time decision, not a per-run side effect.
- **Artifact path assumption.** After a successful invocation, the skill expects `coverage/coverage.xml` at the project root when using the default config block. If a project pins a different output path, its probe-1 (`package.json` script) or probe-2 (vitest config) configuration must make that explicit.

## Presentation Notes

The skill's rendering invariants are language-independent and defined in the main `SKILL.md`. TypeScript-specific notes:

- **Repo-relative paths for `path` column.** Prefer paths like `src/foo/bar.ts` over absolute paths. Vitest's coverage reporters emit repo-relative paths under the default config block — use them as-is.
- **Exclude test files from the per-file breakdown by default.** Test files measuring themselves inflate the table without insight. The default config block below excludes `**/*.test.ts`, `**/*.spec.ts`, and similar patterns via `exclude`; renderers can trust that and skip explicit filtering.
- **`covered/total` uses line counts, not branch counts.** The skill's `covered/total` column uses the line ratio to keep the visual consistent across languages. Branch coverage, when present, belongs in an optional separate row or surface — not the default per-file table.
- **V8 vs Istanbul.** The default provider is `@vitest/coverage-v8` (fast, built-in, no instrumentation overhead). If branch accuracy is insufficient for the project, switching to `@vitest/coverage-istanbul` adds instrumentation-based branch tracking at the cost of slower test runs. See the Istanbul section below.

## Default Coverage Config Block

Copy the block below into the project's `vitest.config.ts`. When present, `vitest run --coverage` produces coverage artifacts under `coverage/` at the project root.

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    coverage: {
      // --- test-coverage skill: default TypeScript coverage config ----------
      // Provider: V8 (fast, built-in; no instrumentation overhead).
      // Switch to 'istanbul' if branch accuracy proves insufficient.
      provider: 'v8',

      // Reporters: xml for metrics pipeline + text-summary for terminal.
      // lcov is optional but useful for HTML browsing: add 'lcov' to this list.
      reporter: ['text-summary', 'xml'],

      // Canonical artifact path. Changing this may break downstream discovery.
      reportsDirectory: './coverage',

      // Source files to measure. Adjust glob to your project layout.
      include: ['src/**/*.{ts,tsx}'],

      // Exclude test files, type-only files, and generated artifacts.
      exclude: [
        '**/*.test.{ts,tsx}',
        '**/*.spec.{ts,tsx}',
        '**/__tests__/**',
        '**/node_modules/**',
        '**/dist/**',
        '**/build/**',
        '**/*.d.ts',
      ],

      // Coverage thresholds. The run exits non-zero when any threshold is
      // breached. Remove or adjust per project policy; no default floor is
      // prescribed because the floor is a policy decision, not a mechanical default.
      // thresholds: {
      //   lines: 80,
      //   functions: 80,
      //   branches: 70,
      //   statements: 80,
      // },
      // --- end test-coverage skill defaults ----------------------------------
    },
  },
})
```

**Tool ownership.** The project still needs `@vitest/coverage-v8` declared as a real dev dependency:

```json
{
  "devDependencies": {
    "vitest": "^4.x",
    "@vitest/coverage-v8": "^4.x"
  }
}
```

Or with the `package.json` coverage script:

```json
{
  "scripts": {
    "test": "vitest run",
    "coverage": "vitest run --coverage"
  }
}
```

The skill does not manage these declarations — the project does.

**Activating thresholds.** Uncomment the `thresholds` block in the config above and set per-project floors. Vitest exits non-zero when any threshold is breached, making threshold failures visible in CI without additional tooling.

**CI integration.** Add `coverage` to the CI step:

```yaml
# GitHub Actions example
- name: Test with coverage
  run: npm run coverage
# or directly:
- run: npx vitest run --coverage
```

## Istanbul Provider — When V8 Branch Accuracy Is Insufficient

V8's built-in coverage can under-report branches in transpiled code (e.g., optional chaining, nullish coalescing, decorator transforms). If branch metrics look implausibly high or uncovered branches are invisible to V8, switch to Istanbul instrumentation:

**Install:**

```json
{
  "devDependencies": {
    "@vitest/coverage-istanbul": "^4.x"
  }
}
```

**Config change** (one line diff):

```diff
-      provider: 'v8',
+      provider: 'istanbul',
```

Istanbul instruments source at the AST level before execution, producing more accurate branch data. The trade-off is slower test runs (instrumentation overhead). For most projects, V8 accuracy with AST-based remapping (added in Vitest v3.2.0) is sufficient.

**DEPRECATED — do not use:** `@vitest/coverage-c8` — this package was superseded by `@vitest/coverage-v8` and has not been published in over three years. Any documentation referencing `@vitest/coverage-c8` is stale. The replacement is `@vitest/coverage-v8`.

## Next.js / React Coverage Notes

Next.js projects using the App Router introduce coverage caveats that do not apply to plain TypeScript or client-only React:

- **Server Components (RSC) cannot be rendered in JSDOM.** Vitest's default environment is JSDOM (browser-like), which does not support the RSC rendering model. Unit tests that import Server Components will either fail to render or silently skip RSC-specific code paths. Coverage numbers for Server Component files may be understated as a result.
- **RSC coverage requires integration-level tests.** To cover Server Component code paths accurately, use route-handler tests (Playwright or similar E2E tooling hitting the running Next.js server) rather than Vitest unit tests with JSDOM. These integration tests produce coverage through actual HTTP handling, not a simulated browser environment.
- **`next.config` instrumentation.** For Vitest to process Next.js files correctly, configure `@vitejs/plugin-react` (or `@vitejs/plugin-react-swc`) and set `environment: 'jsdom'` in `vitest.config.ts`. The `next/jest` config adapter is not required and should not be used in Vitest projects.
- **Exclude `app/` route segments from unit-test thresholds.** Because RSC files are not fully testable with JSDOM, setting aggressive line thresholds on `app/**` without E2E coverage will cause false threshold failures. Either exclude `app/` from Vitest coverage scope and rely on E2E reports for those paths, or set a separate lower threshold for `app/**` if your coverage reporter supports per-directory floors.

## Related Artifacts

- [`test-coverage`](../SKILL.md) skill — dispatcher and renderer (language-agnostic entry point)
- [`typescript-development`](../../typescript-development/SKILL.md) skill — TypeScript conventions (tsc, Biome, project configuration)
- [`testing-strategy`](../../testing-strategy/SKILL.md) skill — coverage philosophy (coverage as discovery tool, not target)
