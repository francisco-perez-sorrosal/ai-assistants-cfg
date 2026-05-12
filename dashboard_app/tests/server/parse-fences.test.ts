import { describe, expect, it } from "vitest";

import { splitAacRegions } from "@/server/aac/parse-fences";

describe("splitAacRegions", () => {
  it("parses a generated fence followed by an authored fence", () => {
    const md = [
      '<!-- aac:generated source=docs/diagrams/system.c4 view=L1Components -->',
      "| Component | Responsibility |",
      "| --- | --- |",
      "<!-- aac:end -->",
      '<!-- aac:authored owner=systems-architect last-reviewed=2026-04-30 -->',
      "## Design Rationale",
      "Some text.",
      "<!-- aac:end -->"
    ].join("\n");

    const regions = splitAacRegions(md);

    // generated + optional plain separator + authored
    const gen = regions.find((r) => r.kind === "generated");
    expect(gen).toBeDefined();
    expect(gen?.attrs["source"]).toBe("docs/diagrams/system.c4");
    expect(gen?.attrs["view"]).toBe("L1Components");
    expect(gen?.content).toContain("Component");

    const auth = regions.find((r) => r.kind === "authored");
    expect(auth).toBeDefined();
    expect(auth?.attrs["owner"]).toBe("systems-architect");
    expect(auth?.attrs["last-reviewed"]).toBe("2026-04-30");
    expect(auth?.content).toContain("Design Rationale");
  });

  it("treats content outside fences as plain kind", () => {
    const md = [
      "# Architecture Guide",
      "",
      "<!-- aac:generated source=x.c4 view=L0 -->",
      "table content",
      "<!-- aac:end -->",
      "",
      "Trailing prose."
    ].join("\n");

    const regions = splitAacRegions(md);

    const plainRegions = regions.filter((r) => r.kind === "plain");
    expect(plainRegions.length).toBeGreaterThanOrEqual(1);
    expect(plainRegions.some((r) => r.content.includes("Architecture Guide"))).toBe(true);
    expect(plainRegions.some((r) => r.content.includes("Trailing prose."))).toBe(true);
  });

  it("returns a single plain region for markdown with no fences", () => {
    const md = "# No fences here\n\nJust prose.";

    const regions = splitAacRegions(md);

    expect(regions).toHaveLength(1);
    expect(regions[0]?.kind).toBe("plain");
    expect(regions[0]?.content).toBe(md);
  });

  it("parses quoted attribute values", () => {
    const md = '<!-- aac:generated source="path with spaces/file.c4" view="My View" -->\ncontent\n<!-- aac:end -->';

    const regions = splitAacRegions(md);
    expect(regions).toHaveLength(1);
    expect(regions[0]?.attrs["source"]).toBe("path with spaces/file.c4");
    expect(regions[0]?.attrs["view"]).toBe("My View");
  });

  it("degrades gracefully on a dangling opener (no aac:end)", () => {
    const md = '<!-- aac:authored owner=me -->\nContent without closer.';

    expect(() => splitAacRegions(md)).not.toThrow();

    const regions = splitAacRegions(md);
    // Should have at least one authored region with the dangling content
    const authored = regions.find((r) => r.kind === "authored");
    expect(authored).toBeDefined();
    expect(authored?.content).toContain("Content without closer.");
  });

  it("degrades gracefully on a dangling closer (no opener)", () => {
    const md = "Some plain content.\n<!-- aac:end -->\nMore plain content.";

    expect(() => splitAacRegions(md)).not.toThrow();

    const regions = splitAacRegions(md);
    // Dangling closer is skipped; remaining content is plain
    expect(regions.every((r) => r.kind === "plain")).toBe(true);
  });

  it("returns empty array for empty input", () => {
    const regions = splitAacRegions("");
    expect(regions).toHaveLength(0);
  });

  it("returns a plain region for whitespace-only input", () => {
    const regions = splitAacRegions("   \n  ");
    expect(regions.every((r) => r.kind === "plain")).toBe(true);
  });

  it("handles multiple fences in sequence with plain text between", () => {
    const md = [
      "Intro.",
      "<!-- aac:generated source=a.c4 view=L0 -->",
      "generated content",
      "<!-- aac:end -->",
      "Middle text.",
      "<!-- aac:authored owner=me -->",
      "authored content",
      "<!-- aac:end -->",
      "Outro."
    ].join("\n");

    const regions = splitAacRegions(md);

    const kinds = regions.map((r) => r.kind);
    expect(kinds).toContain("plain");
    expect(kinds).toContain("generated");
    expect(kinds).toContain("authored");

    // Verify order
    const genIdx = regions.findIndex((r) => r.kind === "generated");
    const authIdx = regions.findIndex((r) => r.kind === "authored");
    expect(genIdx).toBeLessThan(authIdx);
  });

  it("returns empty attrs record when opener has no attributes", () => {
    const md = "<!-- aac:authored -->\nContent\n<!-- aac:end -->";

    const regions = splitAacRegions(md);
    expect(regions).toHaveLength(1);
    expect(regions[0]?.kind).toBe("authored");
    expect(regions[0]?.attrs).toEqual({});
  });
});
