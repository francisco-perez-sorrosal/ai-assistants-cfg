"use client";

import { usePanZoom } from "./use-pan-zoom";

// ─── Props ───────────────────────────────────────────────────────────────────

type DiagramViewerProps = {
  /** Pre-sanitized SVG markup — caller must run sanitizeSvg before passing */
  readonly svg: string;
  readonly label?: string;
  readonly minZoom?: number;
  readonly maxZoom?: number;
};

// ─── Component ───────────────────────────────────────────────────────────────

export function DiagramViewer({
  svg,
  label = "Diagram viewer",
  minZoom,
  maxZoom
}: DiagramViewerProps) {
  const {
    containerRef,
    transform,
    onWheel,
    onPointerDown,
    onPointerMove,
    onPointerUp,
    onKeyDown,
    reset
  } = usePanZoom({ minZoom, maxZoom });

  const transformStyle = `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`;

  return (
    <div className="diagram-viewer-root">
      <div
        ref={containerRef}
        className="diagram-viewer-container"
        role="region"
        aria-label={label}
        tabIndex={0}
        onWheel={onWheel}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onKeyDown={onKeyDown}
      >
        <div
          data-pan-zoom-content
          className="diagram-viewer-transform"
          style={{ transform: transformStyle, transformOrigin: "0 0" }}
          // eslint-disable-next-line react/no-danger
          dangerouslySetInnerHTML={{ __html: svg }}
        />
      </div>
      <div className="diagram-viewer-controls">
        <button
          type="button"
          className="diagram-viewer-reset"
          aria-label="Reset diagram to fit"
          onClick={reset}
        >
          Reset
        </button>
        <span className="diagram-viewer-hint">
          scroll to zoom · drag to pan · Reset to fit
        </span>
      </div>
    </div>
  );
}
