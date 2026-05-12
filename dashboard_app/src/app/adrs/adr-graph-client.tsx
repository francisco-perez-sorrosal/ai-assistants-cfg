"use client";

import { DecisionGraph } from "@/components/viz/decision-graph";
import type { AdrGraphNode } from "@/server/view-models/adr-graph";

// ─── Props ────────────────────────────────────────────────────────────────────

type AdrGraphClientProps = {
  readonly nodes: AdrGraphNode[];
};

// ─── Component ────────────────────────────────────────────────────────────────

/**
 * Thin client wrapper around DecisionGraph that wires onSelect to scroll to
 * the corresponding ArtifactCard in the list below.
 */
export function AdrGraphClient({ nodes }: AdrGraphClientProps) {
  function handleSelect(id: string): void {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return <DecisionGraph nodes={nodes} onSelect={handleSelect} />;
}
