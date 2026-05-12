import { describe, expect, it } from "vitest";

import {
  clampScale,
  fitTransform,
  panByKey,
  zoomAtCursor
} from "@/components/viz/use-pan-zoom";

// ─── clampScale ──────────────────────────────────────────────────────────────

describe("clampScale — enforces [minZoom, maxZoom] bounds", () => {
  it("returns the value unchanged when within bounds", () => {
    expect(clampScale(1.5, 0.25, 8)).toBe(1.5);
  });

  it("clamps to minZoom when value is below lower bound", () => {
    expect(clampScale(0.1, 0.25, 8)).toBe(0.25);
  });

  it("clamps to maxZoom when value exceeds upper bound", () => {
    expect(clampScale(10, 0.25, 8)).toBe(8);
  });

  it("returns exact boundary when value equals minZoom", () => {
    expect(clampScale(0.25, 0.25, 8)).toBe(0.25);
  });

  it("returns exact boundary when value equals maxZoom", () => {
    expect(clampScale(8, 0.25, 8)).toBe(8);
  });
});

// ─── zoomAtCursor ────────────────────────────────────────────────────────────

describe("zoomAtCursor — cursor world position stays fixed under zoom", () => {
  it("zooms in (positive delta reduces scale, negative factor) at the cursor", () => {
    // delta > 0 → scrolling down → zooming out, factor < 1
    // delta < 0 → scrolling up → zooming in, factor > 1
    const current = { x: 0, y: 0, scale: 1 };
    const result = zoomAtCursor(current, 50, 50, -100, 0.25, 8);
    expect(result.scale).toBeGreaterThan(1);
    // Cursor at (50,50) stays fixed: newX + (50) * newScale/oldScale offset applied
    // After scale changes, cursor world position is preserved
    const worldXBefore = (50 - current.x) / current.scale;
    const worldXAfter = (50 - result.x) / result.scale;
    expect(worldXAfter).toBeCloseTo(worldXBefore, 5);
  });

  it("zooms out (positive delta) producing a smaller scale", () => {
    const current = { x: 0, y: 0, scale: 2 };
    const result = zoomAtCursor(current, 100, 100, 200, 0.25, 8);
    expect(result.scale).toBeLessThan(2);
  });

  it("clamps scale at maxZoom when zooming beyond the upper bound", () => {
    const current = { x: 0, y: 0, scale: 7.9 };
    const result = zoomAtCursor(current, 50, 50, -5000, 0.25, 8);
    expect(result.scale).toBe(8);
  });

  it("clamps scale at minZoom when zooming beyond the lower bound", () => {
    const current = { x: 0, y: 0, scale: 0.3 };
    const result = zoomAtCursor(current, 50, 50, 5000, 0.25, 8);
    expect(result.scale).toBe(0.25);
  });

  it("preserves cursor world position when zooming in at an offset cursor", () => {
    const current = { x: 20, y: 30, scale: 1 };
    const cursorX = 80;
    const cursorY = 60;
    const result = zoomAtCursor(current, cursorX, cursorY, -100, 0.25, 8);

    const worldXBefore = (cursorX - current.x) / current.scale;
    const worldYBefore = (cursorY - current.y) / current.scale;
    const worldXAfter = (cursorX - result.x) / result.scale;
    const worldYAfter = (cursorY - result.y) / result.scale;

    expect(worldXAfter).toBeCloseTo(worldXBefore, 5);
    expect(worldYAfter).toBeCloseTo(worldYBefore, 5);
  });
});

// ─── fitTransform ────────────────────────────────────────────────────────────

describe("fitTransform — centers and fits content within container", () => {
  it("scales down content that exceeds container dimensions", () => {
    const result = fitTransform(400, 300, 800, 600);
    // Scale must be ≤ 1 because content is larger than container
    expect(result.scale).toBeLessThanOrEqual(1);
    // Content must fit entirely — no dimension exceeds container
    expect(result.scale * 800).toBeLessThanOrEqual(400 + 0.001);
    expect(result.scale * 600).toBeLessThanOrEqual(300 + 0.001);
  });

  it("does not scale up content smaller than the container", () => {
    const result = fitTransform(400, 300, 100, 80);
    expect(result.scale).toBe(1);
  });

  it("centers content horizontally when constrained by height", () => {
    // A tall narrow SVG: 100×400 in a 400×300 container
    // Scale limited by height: 300/400 = 0.75; scaled width = 75
    const result = fitTransform(400, 300, 100, 400);
    const scaledW = 100 * result.scale;
    const expectedX = (400 - scaledW) / 2;
    expect(result.x).toBeCloseTo(expectedX, 5);
  });

  it("centers content vertically when constrained by width", () => {
    // A wide flat SVG: 800×100 in a 400×300 container
    // Scale limited by width: 400/800 = 0.5; scaled height = 50
    const result = fitTransform(400, 300, 800, 100);
    const scaledH = 100 * result.scale;
    const expectedY = (300 - scaledH) / 2;
    expect(result.y).toBeCloseTo(expectedY, 5);
  });

  it("returns identity transform for zero-dimension content", () => {
    const result = fitTransform(400, 300, 0, 0);
    expect(result).toEqual({ x: 0, y: 0, scale: 1 });
  });

  it("produces an exact fit when content matches container", () => {
    const result = fitTransform(400, 300, 400, 300);
    expect(result.scale).toBeCloseTo(1, 5);
    expect(result.x).toBeCloseTo(0, 5);
    expect(result.y).toBeCloseTo(0, 5);
  });
});

// ─── panByKey ────────────────────────────────────────────────────────────────

describe("panByKey — arrow-key pan moves translate by 20px", () => {
  const base = { x: 0, y: 0, scale: 1 };

  it("ArrowLeft moves content right (x increases by 20px)", () => {
    const result = panByKey(base, "ArrowLeft");
    expect(result.x).toBe(20);
    expect(result.y).toBe(0);
    expect(result.scale).toBe(1);
  });

  it("ArrowRight moves content left (x decreases by 20px)", () => {
    const result = panByKey(base, "ArrowRight");
    expect(result.x).toBe(-20);
    expect(result.y).toBe(0);
  });

  it("ArrowUp moves content down (y increases by 20px)", () => {
    const result = panByKey(base, "ArrowUp");
    expect(result.x).toBe(0);
    expect(result.y).toBe(20);
  });

  it("ArrowDown moves content up (y decreases by 20px)", () => {
    const result = panByKey(base, "ArrowDown");
    expect(result.x).toBe(0);
    expect(result.y).toBe(-20);
  });

  it("preserves the existing scale across a pan operation", () => {
    const t = { x: 10, y: 5, scale: 2.5 };
    const result = panByKey(t, "ArrowLeft");
    expect(result.scale).toBe(2.5);
  });

  it("accumulates correctly across multiple pans", () => {
    let t = base;
    t = panByKey(t, "ArrowLeft");
    t = panByKey(t, "ArrowLeft");
    t = panByKey(t, "ArrowDown");
    expect(t.x).toBe(40);
    expect(t.y).toBe(-20);
  });
});
