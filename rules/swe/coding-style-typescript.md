---
paths: ["**/*.ts", "**/*.tsx", "**/*.mts", "**/*.cts"]
---

## TypeScript Coding Style

Path-scoped — loaded only when editing TypeScript files.

For toolchain setup, Biome vs. ESLint decision, and full `tsconfig.json` guidance, see
[`skills/typescript-development/contexts/typescript.md`](../../skills/typescript-development/contexts/typescript.md).

### Strict Mode (mandatory)

Every `tsconfig.json` must enable:

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true
  }
}
```

`strict` enables the full strict family (`strictNullChecks`, `strictFunctionTypes`, etc.).
`noUncheckedIndexedAccess` ensures array/object indexing returns `T | undefined`, preventing silent runtime errors on out-of-bounds access.

### `any` Usage

- **No `any` without an explicit disable comment and a reason**:
  ```typescript
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- third-party callback has no typings
  const handler: any = thirdPartyLib.registerCallback(fn);
  ```
- **Prefer `unknown`** for genuinely-unknown values — it forces a type-narrowing check before use, unlike `any` which silently bypasses the type system.

### Import Ordering

Keep imports sorted consistently. Tool choice depends on the project's code-quality toolchain (see context link above):

- **Biome projects**: Biome's built-in import sorter (`biome check --write`) — no extra config needed.
- **ESLint projects**: `eslint-plugin-import` with `import/order` rule configured.

Do not mix both sorters in one project.

### Exports

Prefer **named exports** over default exports:

```typescript
// preferred
export function parseConfig(raw: unknown): Config { ... }
export type Config = { ... };

// avoid
export default function parseConfig(raw: unknown): Config { ... }
```

Named exports produce more stable import paths across renames and enable better IDE auto-import. Default exports are acceptable only when a framework convention requires them (e.g., Next.js page components, React lazy boundaries).
