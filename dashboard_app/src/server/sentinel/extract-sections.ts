import "server-only";

import { parseMarkdownTable } from "@/server/parsers/markdown-table";

export type SentinelSections = {
  critical: string;
  important: string;
  suggested: string;
  rest: string;
};

export type SentinelLogPoint = {
  timestamp: string | null;
  grade: string | null;
  critical: number | null;
  important: number | null;
  suggested: number | null;
  coherence: string | null;
};

// Matches a finding section heading: any # depth followed by critical/important/suggested.
const FINDING_SECTION_PATTERN = /^(#{1,6})\s+(critical|important|suggested)\b/i;

// Matches a heading that terminates an open finding section:
// same or shallower level than ### (i.e. ## or #), OR another finding section heading.
const SECTION_TERMINATOR_PATTERN = /^#{1,2}\s+\S/;

/**
 * Splits a sentinel report body into its three finding sections and a remainder.
 *
 * Tolerant matching: recognises the keyword at the start of any heading level,
 * regardless of trailing text (e.g. "### Critical (blocks correct behavior)").
 *
 * A finding section ends at:
 * - the next finding section heading (critical / important / suggested), OR
 * - a shallower heading (`##` or `#`), which signals a new top-level section.
 *
 * If a heading is not found the corresponding field is "".
 */
export function extractSections(reportBody: string): SentinelSections {
  const lines = reportBody.split("\n");

  type SectionKind = "critical" | "important" | "suggested";

  // First pass: find all section-boundary line indices.
  // A boundary is either a finding keyword heading OR a shallower (#/##+) heading.
  const boundaries: Array<{ kind: SectionKind | null; lineIndex: number }> = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i] ?? "";
    const findingMatch = FINDING_SECTION_PATTERN.exec(line);
    if (findingMatch) {
      const keyword = findingMatch[2]?.toLowerCase() as SectionKind | undefined;
      if (keyword === "critical" || keyword === "important" || keyword === "suggested") {
        boundaries.push({ kind: keyword, lineIndex: i });
      }
      continue;
    }
    // A shallower heading while inside a finding section acts as a terminator.
    if (SECTION_TERMINATOR_PATTERN.test(line)) {
      boundaries.push({ kind: null, lineIndex: i });
    }
  }

  const sections: Record<SectionKind, string> = { critical: "", important: "", suggested: "" };
  const sectionLineRanges: Array<{ kind: SectionKind; start: number; end: number }> = [];

  let activeFinding: SectionKind | null = null;
  let activeStart = 0;

  for (const boundary of boundaries) {
    if (activeFinding !== null) {
      // Close the previous finding section at the current boundary line.
      sectionLineRanges.push({ kind: activeFinding, start: activeStart, end: boundary.lineIndex });
      sections[activeFinding] = lines.slice(activeStart, boundary.lineIndex).join("\n");
      activeFinding = null;
    }
    if (boundary.kind !== null) {
      activeFinding = boundary.kind;
      activeStart = boundary.lineIndex;
    }
  }

  // Close the last open finding section at end of body.
  if (activeFinding !== null) {
    sectionLineRanges.push({ kind: activeFinding, start: activeStart, end: lines.length });
    sections[activeFinding] = lines.slice(activeStart).join("\n");
  }

  // rest = everything NOT in one of the three sections
  const inSectionSet = new Set<number>();
  for (const range of sectionLineRanges) {
    for (let i = range.start; i < range.end; i++) {
      inSectionSet.add(i);
    }
  }

  const restLines: string[] = [];
  for (let i = 0; i < lines.length; i++) {
    if (!inSectionSet.has(i)) {
      restLines.push(lines[i] ?? "");
    }
  }

  return {
    critical: sections.critical,
    important: sections.important,
    suggested: sections.suggested,
    rest: restLines.join("\n")
  };
}

/**
 * Parses SENTINEL_LOG.md's markdown table into a typed array of log points.
 *
 * Column mapping (case-insensitive header lookup):
 *   Timestamp           → timestamp
 *   Health Grade        → grade
 *   Findings (C/I/S)    → critical, important, suggested  (split on "/")
 *   Ecosystem Coherence → coherence
 *
 * Non-numeric or absent cells coerce to null.
 */
export function parseSentinelLog(logBody: string): SentinelLogPoint[] {
  const rows = parseMarkdownTable(logBody);
  return rows.map((row) => {
    const findingsRaw = findColumn(row, "Findings (C/I/S)") ?? "";
    const [c, i, s] = findingsRaw.split("/").map((part) => part.trim());
    return {
      timestamp: toStringCell(findColumn(row, "Timestamp")),
      grade: toStringCell(findColumn(row, "Health Grade")),
      critical: toNumberCell(c),
      important: toNumberCell(i),
      suggested: toNumberCell(s),
      coherence: toStringCell(findColumn(row, "Ecosystem Coherence"))
    };
  });
}

/**
 * Case-insensitive column lookup — tolerates minor header capitalisation drift.
 */
function findColumn(row: Record<string, string>, name: string): string | undefined {
  const lower = name.toLowerCase();
  for (const [key, value] of Object.entries(row)) {
    if (key.toLowerCase() === lower) {
      return value;
    }
  }
  return undefined;
}

function toStringCell(cell: string | undefined): string | null {
  if (cell === undefined || cell.trim() === "") {
    return null;
  }
  return cell.trim();
}

function toNumberCell(cell: string | undefined): number | null {
  if (cell === undefined || cell.trim() === "") {
    return null;
  }
  const parsed = Number(cell.trim());
  return Number.isFinite(parsed) ? parsed : null;
}
