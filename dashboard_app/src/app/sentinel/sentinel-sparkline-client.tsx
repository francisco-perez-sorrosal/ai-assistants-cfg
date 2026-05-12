"use client";

import { Sparkline } from "@/components/viz/sparkline";

// ─── Grade → color mapping ────────────────────────────────────────────────────

const GRADE_COLOR_TOKENS: Record<number, string> = {
  4: "var(--grade-a)",
  3: "var(--grade-b)",
  2: "var(--grade-c)",
  1: "var(--grade-d)"
};

function gradeColorForNumber(y: number): string {
  return GRADE_COLOR_TOKENS[Math.round(y)] ?? "var(--color-text-muted)";
}

// ─── Props ────────────────────────────────────────────────────────────────────

type SentinelSparklineClientProps = {
  readonly points: Array<{ x: string; y: number | null }>;
};

// ─── Component ───────────────────────────────────────────────────────────────

/**
 * Client wrapper that owns the grade→color closure so the server component
 * never passes a function across the server→client boundary.
 */
export function SentinelSparklineClient({ points }: SentinelSparklineClientProps) {
  return (
    <Sparkline
      series={[
        {
          label: "Health",
          color: "var(--color-accent)",
          points
        }
      ]}
      colorForValue={gradeColorForNumber}
    />
  );
}
