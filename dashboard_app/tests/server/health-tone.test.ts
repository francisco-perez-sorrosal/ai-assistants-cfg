/**
 * Behavioral tests for `src/lib/health-tone.ts`.
 *
 * Behaviors validated:
 *   - healthSummary: all-good → "IMPROVING"; any-bad → "WORSENING";
 *     mixed/steady → "STABLE"; isBaseline flag → "BASELINE CAPTURED";
 *     degradedCollectors → degradedNote mentions the tool name.
 *
 * Implementation contract notes (discovered from src/lib/health-tone.ts):
 *   - healthSummary "BASELINE CAPTURED" requires opts.isBaseline === true.
 *     An empty tones array without the flag returns "STABLE".
 *   - Degraded-collector note is in the `degradedNote` field, not in `label`.
 *   - Any single "bad" tone triggers "WORSENING" (not a majority rule).
 *
 * Environment: vitest node — deferred imports allow RED collection when the
 * module does not exist yet (concurrent BDD/TDD).
 */

import { describe, expect, it } from "vitest";

// ---------------------------------------------------------------------------
// healthSummary — aggregate tone from a collection of per-metric tones
// ---------------------------------------------------------------------------

describe("healthSummary", () => {
  it("returns 'IMPROVING' label when all tones are 'good'", async () => {
    const { healthSummary } = await import("@/lib/health-tone");
    const result = healthSummary(["good", "good", "good", "good"]);
    expect(result.label).toBe("IMPROVING");
  });

  it("returns 'WORSENING' label when any tone is 'bad' (even one in four)", async () => {
    const { healthSummary } = await import("@/lib/health-tone");
    // Implementation: any bad → WORSENING
    const result = healthSummary(["bad", "bad", "bad", "good"]);
    expect(result.label).toBe("WORSENING");
  });

  it("returns 'WORSENING' label when even one tone is 'bad' in a mixed set", async () => {
    const { healthSummary } = await import("@/lib/health-tone");
    const result = healthSummary(["good", "bad", "steady", "good"]);
    expect(result.label).toBe("WORSENING");
  });

  it("returns 'STABLE' label when tones are a mix of good and steady with no bad", async () => {
    const { healthSummary } = await import("@/lib/health-tone");
    // 1 good out of 4 is < ceil(4/2)=2, so no majority → STABLE
    const result = healthSummary(["good", "steady", "steady", "steady"]);
    expect(result.label).toBe("STABLE");
  });

  it("returns 'STABLE' label for an empty tones array (no crash)", async () => {
    const { healthSummary } = await import("@/lib/health-tone");
    // Empty array without isBaseline flag → STABLE (not BASELINE CAPTURED)
    expect(() => healthSummary([])).not.toThrow();
    expect(healthSummary([]).label).toBe("STABLE");
  });

  it("returns 'BASELINE CAPTURED' label when isBaseline option is true", async () => {
    const { healthSummary } = await import("@/lib/health-tone");
    const result = healthSummary(["neutral", "neutral", "neutral", "neutral"], {
      isBaseline: true
    });
    expect(result.label).toBe("BASELINE CAPTURED");
  });

  it("returns 'BASELINE CAPTURED' even with empty tones when isBaseline is true", async () => {
    const { healthSummary } = await import("@/lib/health-tone");
    const result = healthSummary([], { isBaseline: true });
    expect(result.label).toBe("BASELINE CAPTURED");
  });

  it("sets degraded to true and degradedNote to a non-null string when degradedCollectors is non-empty", async () => {
    const { healthSummary } = await import("@/lib/health-tone");
    const result = healthSummary(["good", "good", "good", "good"], {
      degradedCollectors: ["ruff"]
    });
    expect(result.degraded).toBe(true);
    expect(result.degradedNote).not.toBeNull();
  });

  it("includes the degraded tool name in degradedNote when degradedCollectors is non-empty", async () => {
    const { healthSummary } = await import("@/lib/health-tone");
    const result = healthSummary(["good", "good", "good", "good"], {
      degradedCollectors: ["ruff"]
    });
    expect(result.degradedNote).toContain("ruff");
    // The note must also mention data confidence in some form
    const noteLower = (result.degradedNote ?? "").toLowerCase();
    expect(noteLower).toContain("confidence");
  });

  it("sets degraded to false and degradedNote to null when no degraded collectors", async () => {
    const { healthSummary } = await import("@/lib/health-tone");
    const result = healthSummary(["good", "good", "good", "good"]);
    expect(result.degraded).toBe(false);
    expect(result.degradedNote).toBeNull();
  });
});
