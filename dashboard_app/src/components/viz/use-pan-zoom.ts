"use client";

import { useCallback, useRef, useState } from "react";

// ─── Types ──────────────────────────────────────────────────────────────────

export type Transform = {
  readonly x: number;
  readonly y: number;
  readonly scale: number;
};

export type PanZoomOptions = {
  readonly minZoom?: number;
  readonly maxZoom?: number;
};

export type PanZoomResult = {
  readonly containerRef: React.RefObject<HTMLDivElement | null>;
  readonly transform: Transform;
  readonly onWheel: (e: React.WheelEvent<HTMLDivElement>) => void;
  readonly onPointerDown: (e: React.PointerEvent<HTMLDivElement>) => void;
  readonly onPointerMove: (e: React.PointerEvent<HTMLDivElement>) => void;
  readonly onPointerUp: (e: React.PointerEvent<HTMLDivElement>) => void;
  readonly onKeyDown: (e: React.KeyboardEvent<HTMLDivElement>) => void;
  readonly reset: () => void;
  readonly zoomIn: () => void;
  readonly zoomOut: () => void;
};

// ─── Pure math helpers (exported for testing) ────────────────────────────────

const MIN_ZOOM_DEFAULT = 0.25;
const MAX_ZOOM_DEFAULT = 8;
const PAN_STEP_PX = 20;
const ZOOM_STEP = 0.2;
const WHEEL_SENSITIVITY = 0.001;

export function clampScale(
  scale: number,
  minZoom: number,
  maxZoom: number
): number {
  return Math.min(Math.max(scale, minZoom), maxZoom);
}

/**
 * Compute the new transform when zooming toward a cursor point.
 * The cursor's world position stays fixed under the zoom.
 */
export function zoomAtCursor(
  current: Transform,
  cursorX: number,
  cursorY: number,
  delta: number,
  minZoom: number,
  maxZoom: number
): Transform {
  const factor = 1 - delta * WHEEL_SENSITIVITY;
  const newScale = clampScale(current.scale * factor, minZoom, maxZoom);
  const scaleRatio = newScale / current.scale;
  const newX = cursorX - (cursorX - current.x) * scaleRatio;
  const newY = cursorY - (cursorY - current.y) * scaleRatio;
  return { x: newX, y: newY, scale: newScale };
}

/**
 * Compute transform that centers and fits content within a container.
 * The scale is uniform so the content is fully visible.
 */
export function fitTransform(
  containerWidth: number,
  containerHeight: number,
  contentWidth: number,
  contentHeight: number
): Transform {
  if (contentWidth === 0 || contentHeight === 0) {
    return { x: 0, y: 0, scale: 1 };
  }
  const scale = Math.min(
    containerWidth / contentWidth,
    containerHeight / contentHeight,
    1
  );
  const x = (containerWidth - contentWidth * scale) / 2;
  const y = (containerHeight - contentHeight * scale) / 2;
  return { x, y, scale };
}

/**
 * Compute the new translate after an arrow-key pan.
 * Returns updated x/y only; scale is unchanged.
 */
export function panByKey(
  current: Transform,
  direction: "ArrowLeft" | "ArrowRight" | "ArrowUp" | "ArrowDown"
): Transform {
  switch (direction) {
    case "ArrowLeft":
      return { ...current, x: current.x + PAN_STEP_PX };
    case "ArrowRight":
      return { ...current, x: current.x - PAN_STEP_PX };
    case "ArrowUp":
      return { ...current, y: current.y + PAN_STEP_PX };
    case "ArrowDown":
      return { ...current, y: current.y - PAN_STEP_PX };
  }
}

// ─── Hook ────────────────────────────────────────────────────────────────────

export function usePanZoom(options: PanZoomOptions = {}): PanZoomResult {
  const minZoom = options.minZoom ?? MIN_ZOOM_DEFAULT;
  const maxZoom = options.maxZoom ?? MAX_ZOOM_DEFAULT;

  const containerRef = useRef<HTMLDivElement | null>(null);
  const [transform, setTransform] = useState<Transform>({ x: 0, y: 0, scale: 1 });

  // Pointer tracking for drag-to-pan and pinch-zoom
  const activePointers = useRef<Map<number, { x: number; y: number }>>(
    new Map()
  );
  const lastPinchDistance = useRef<number | null>(null);

  // ── Wheel zoom ─────────────────────────────────────────────────────────────
  const onWheel = useCallback(
    (e: React.WheelEvent<HTMLDivElement>) => {
      e.preventDefault();
      const rect = e.currentTarget.getBoundingClientRect();
      const cursorX = e.clientX - rect.left;
      const cursorY = e.clientY - rect.top;
      setTransform((prev) =>
        zoomAtCursor(prev, cursorX, cursorY, e.deltaY, minZoom, maxZoom)
      );
    },
    [minZoom, maxZoom]
  );

  // ── Pointer drag / pinch ───────────────────────────────────────────────────
  const onPointerDown = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      e.currentTarget.setPointerCapture(e.pointerId);
      activePointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (activePointers.current.size === 2) {
        const pts = Array.from(activePointers.current.values());
        const p0 = pts[0];
        const p1 = pts[1];
        if (p0 && p1) {
          lastPinchDistance.current = Math.hypot(
            p1.x - p0.x,
            p1.y - p0.y
          );
        }
      }
    },
    []
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      const prev = activePointers.current.get(e.pointerId);
      if (!prev) return;

      if (activePointers.current.size === 1) {
        // Single-pointer drag-to-pan
        const dx = e.clientX - prev.x;
        const dy = e.clientY - prev.y;
        setTransform((t) => ({ ...t, x: t.x + dx, y: t.y + dy }));
      } else if (activePointers.current.size === 2) {
        // Two-pointer pinch-to-zoom
        activePointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
        const pts = Array.from(activePointers.current.values());
        const p0 = pts[0];
        const p1 = pts[1];
        if (p0 && p1 && lastPinchDistance.current !== null) {
          const newDist = Math.hypot(p1.x - p0.x, p1.y - p0.y);
          const ratio = newDist / lastPinchDistance.current;
          const midX = (p0.x + p1.x) / 2;
          const midY = (p0.y + p1.y) / 2;
          const rect = e.currentTarget.getBoundingClientRect();
          const cursorX = midX - rect.left;
          const cursorY = midY - rect.top;
          setTransform((t) => {
            const newScale = clampScale(t.scale * ratio, minZoom, maxZoom);
            const scaleRatio = newScale / t.scale;
            return {
              x: cursorX - (cursorX - t.x) * scaleRatio,
              y: cursorY - (cursorY - t.y) * scaleRatio,
              scale: newScale
            };
          });
          lastPinchDistance.current = newDist;
        }
      }

      activePointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    },
    [minZoom, maxZoom]
  );

  const onPointerUp = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    activePointers.current.delete(e.pointerId);
    if (activePointers.current.size < 2) {
      lastPinchDistance.current = null;
    }
  }, []);

  // ── Keyboard ───────────────────────────────────────────────────────────────
  const onKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      const arrowKeys = ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"];
      if (arrowKeys.includes(e.key)) {
        e.preventDefault();
        setTransform((t) =>
          panByKey(
            t,
            e.key as "ArrowLeft" | "ArrowRight" | "ArrowUp" | "ArrowDown"
          )
        );
        return;
      }
      if (e.key === "+" || e.key === "=") {
        e.preventDefault();
        setTransform((t) => ({
          ...t,
          scale: clampScale(t.scale + ZOOM_STEP, minZoom, maxZoom)
        }));
        return;
      }
      if (e.key === "-") {
        e.preventDefault();
        setTransform((t) => ({
          ...t,
          scale: clampScale(t.scale - ZOOM_STEP, minZoom, maxZoom)
        }));
        return;
      }
      if (e.key === "0") {
        e.preventDefault();
        reset();
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [minZoom, maxZoom]
  );

  // ── Reset / fit to viewport ────────────────────────────────────────────────
  const reset = useCallback(() => {
    const container = containerRef.current;
    if (!container) {
      setTransform({ x: 0, y: 0, scale: 1 });
      return;
    }
    const innerEl = container.querySelector<HTMLElement>("[data-pan-zoom-content]");
    if (!innerEl) {
      setTransform({ x: 0, y: 0, scale: 1 });
      return;
    }
    const svgEl = innerEl.querySelector("svg");
    const contentW = svgEl?.viewBox.baseVal.width || innerEl.scrollWidth || container.clientWidth;
    const contentH = svgEl?.viewBox.baseVal.height || innerEl.scrollHeight || container.clientHeight;
    setTransform(
      fitTransform(container.clientWidth, container.clientHeight, contentW, contentH)
    );
  }, []);

  const zoomIn = useCallback(() => {
    setTransform((t) => ({
      ...t,
      scale: clampScale(t.scale + ZOOM_STEP, minZoom, maxZoom)
    }));
  }, [minZoom, maxZoom]);

  const zoomOut = useCallback(() => {
    setTransform((t) => ({
      ...t,
      scale: clampScale(t.scale - ZOOM_STEP, minZoom, maxZoom)
    }));
  }, [minZoom, maxZoom]);

  return {
    containerRef,
    transform,
    onWheel,
    onPointerDown,
    onPointerMove,
    onPointerUp,
    onKeyDown,
    reset,
    zoomIn,
    zoomOut
  };
}
