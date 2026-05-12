"use client";

import { shapeChartData, type TrendChartProps, type TrendSeries } from "./trend-chart";
import { Line, LineChart, ResponsiveContainer } from "recharts";

export type SparklineProps = Omit<TrendChartProps, "xLabel"> & {
  compact?: true;
  colorForValue?: (y: number) => string;
};

const SPARKLINE_HEIGHT = 56;
const DOT_RADIUS = 2;

/**
 * Compact line preview — no axes, no grid, no tooltip.
 * Suitable for inline health-grade trends next to the latest sentinel report.
 * `colorForValue` overrides the series color per-render based on the most recent y value.
 */
export function Sparkline({ series, height = SPARKLINE_HEIGHT, colorForValue }: SparklineProps) {
  if (series.length === 0) {
    return null;
  }

  const data = shapeChartData(series);
  if (data.length === 0) {
    return null;
  }

  // If colorForValue is provided, compute stroke from the last non-null y value.
  const resolveColor = (s: TrendSeries): string => {
    if (!colorForValue) {
      return s.color;
    }
    const lastPoint = [...s.points].reverse().find((pt) => pt.y !== null);
    return lastPoint?.y !== undefined && lastPoint.y !== null ? colorForValue(lastPoint.y) : s.color;
  };

  return (
    <div className="sparkline-wrapper">
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
          {series.map((s) => (
            <Line
              key={s.label}
              type="monotone"
              dataKey={s.label}
              stroke={resolveColor(s)}
              strokeWidth={1.5}
              dot={{ r: DOT_RADIUS, fill: resolveColor(s), strokeWidth: 0 }}
              activeDot={false}
              connectNulls={false}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
