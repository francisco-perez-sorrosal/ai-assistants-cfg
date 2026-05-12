import { describe, expect, it } from "vitest";

import {
  RENDERER_REGISTRY,
  resolveRenderer
} from "@/components/registry";
import { DefaultShell } from "@/components/shells/default";
import { ExplanationShell } from "@/components/shells/explanation";
import { ReferenceShell } from "@/components/shells/reference";

// ─── RENDERER_REGISTRY size and coverage ────────────────────────────────────

describe("RENDERER_REGISTRY — six registered keys", () => {
  it("contains at least six keys (tutorial, how-to, reference, explanation, concepts, markdown)", () => {
    expect(RENDERER_REGISTRY.size).toBeGreaterThanOrEqual(6);
  });

  it("registers the reference key", () => {
    expect(RENDERER_REGISTRY.has("reference")).toBe(true);
  });

  it("registers the explanation key", () => {
    expect(RENDERER_REGISTRY.has("explanation")).toBe(true);
  });

  it("registers the markdown key", () => {
    expect(RENDERER_REGISTRY.has("markdown")).toBe(true);
  });

  it("registers the tutorial key", () => {
    expect(RENDERER_REGISTRY.has("tutorial")).toBe(true);
  });

  it("registers the how-to key", () => {
    expect(RENDERER_REGISTRY.has("how-to")).toBe(true);
  });

  it("registers the concepts key", () => {
    expect(RENDERER_REGISTRY.has("concepts")).toBe(true);
  });
});

// ─── resolveRenderer — diataxis match wins ───────────────────────────────────

describe("resolveRenderer — diataxis match takes priority", () => {
  it("returns ReferenceShell for diataxis=reference", () => {
    expect(resolveRenderer("reference")).toBe(ReferenceShell);
  });

  it("returns ExplanationShell for diataxis=explanation", () => {
    expect(resolveRenderer("explanation")).toBe(ExplanationShell);
  });

  it("diataxis match wins over contentType match", () => {
    // Even if contentType would resolve to markdown (DefaultShell),
    // diataxis=reference wins.
    expect(resolveRenderer("reference", "markdown")).toBe(ReferenceShell);
  });
});

// ─── resolveRenderer — Diátaxis aliases map to DefaultShell ─────────────────

describe("resolveRenderer — tutorial/how-to/concepts alias to DefaultShell", () => {
  it("returns DefaultShell for diataxis=tutorial", () => {
    expect(resolveRenderer("tutorial")).toBe(DefaultShell);
  });

  it("returns DefaultShell for diataxis=how-to", () => {
    expect(resolveRenderer("how-to")).toBe(DefaultShell);
  });

  it("returns DefaultShell for diataxis=concepts", () => {
    expect(resolveRenderer("concepts")).toBe(DefaultShell);
  });
});

// ─── resolveRenderer — contentType fallback ──────────────────────────────────

describe("resolveRenderer — falls back to contentType when diataxis is absent", () => {
  it("returns DefaultShell for contentType=markdown with no diataxis", () => {
    expect(resolveRenderer(undefined, "markdown")).toBe(DefaultShell);
  });
});

// ─── resolveRenderer — unknown → DefaultShell ────────────────────────────────

describe("resolveRenderer — unknown values fall back to DefaultShell", () => {
  it("returns DefaultShell for an unrecognized diataxis value", () => {
    expect(resolveRenderer("unknown-type")).toBe(DefaultShell);
  });

  it("returns DefaultShell when both diataxis and contentType are undefined", () => {
    expect(resolveRenderer(undefined, undefined)).toBe(DefaultShell);
  });

  it("returns DefaultShell for an unrecognized contentType with no diataxis", () => {
    expect(resolveRenderer(undefined, "unknown-format")).toBe(DefaultShell);
  });
});
