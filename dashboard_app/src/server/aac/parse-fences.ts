import "server-only";

// ─── Types ────────────────────────────────────────────────────────────────────

export type AacKind = "generated" | "authored" | "plain";

export type AacRegion = {
  readonly kind: AacKind;
  readonly attrs: Record<string, string>;
  readonly content: string;
};

// ─── Constants ────────────────────────────────────────────────────────────────

// Matches: <!-- aac:(generated|authored) ... -->
const OPENER_RE =
  /<!--\s*aac:(generated|authored)(?:\s+(.*?))?\s*-->/g;

// Matches: <!-- aac:end -->
const CLOSER_RE = /<!--\s*aac:end\s*-->/g;

// Matches: key="value" or key=value (no spaces in bare value)
const ATTR_RE = /(\w[\w-]*)=(?:"([^"]*?)"|(\S+))/g;

// ─── Attribute parsing ────────────────────────────────────────────────────────

function parseAttrs(attrString: string): Record<string, string> {
  const result: Record<string, string> = {};
  let match: RegExpExecArray | null;
  ATTR_RE.lastIndex = 0;
  while ((match = ATTR_RE.exec(attrString)) !== null) {
    const key = match[1];
    // match[2] = quoted value, match[3] = bare value
    const value = match[2] ?? match[3] ?? "";
    if (key !== undefined) {
      result[key] = value;
    }
  }
  return result;
}

// ─── Region scanner ───────────────────────────────────────────────────────────

type RawToken =
  | { type: "opener"; kind: "generated" | "authored"; attrs: Record<string, string>; index: number; end: number }
  | { type: "closer"; index: number; end: number };

function tokenize(markdown: string): RawToken[] {
  const tokens: RawToken[] = [];

  // Collect openers
  const openerRe = new RegExp(OPENER_RE.source, "g");
  let m: RegExpExecArray | null;
  while ((m = openerRe.exec(markdown)) !== null) {
    const kind = m[1] as "generated" | "authored";
    const attrString = m[2] ?? "";
    tokens.push({
      type: "opener",
      kind,
      attrs: parseAttrs(attrString),
      index: m.index,
      end: m.index + m[0].length
    });
  }

  // Collect closers
  const closerRe = new RegExp(CLOSER_RE.source, "g");
  while ((m = closerRe.exec(markdown)) !== null) {
    tokens.push({ type: "closer", index: m.index, end: m.index + m[0].length });
  }

  // Sort by position in document
  tokens.sort((a, b) => a.index - b.index);

  return tokens;
}

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Splits a markdown string into typed AaC regions based on fence comments.
 *
 * Handles:
 * - <!-- aac:generated key=val --> ... <!-- aac:end -->
 * - <!-- aac:authored key=val --> ... <!-- aac:end -->
 * - Content outside fences is kind "plain" with empty attrs
 * - Unbalanced openers: content runs to EOF or the next opener
 * - Unbalanced closers: skipped (treated as plain text)
 */
export function splitAacRegions(markdown: string): AacRegion[] {
  const regions: AacRegion[] = [];
  const tokens = tokenize(markdown);

  let cursor = 0;
  let i = 0;

  while (i < tokens.length) {
    const token = tokens[i];
    if (token === undefined) break;

    if (token.type === "closer") {
      // Dangling closer — no matching opener; skip it
      i++;
      continue;
    }

    // Found an opener
    const opener = token;

    // Emit plain region before this opener (if any non-whitespace or we want to preserve all)
    const beforeContent = markdown.slice(cursor, opener.index);
    if (beforeContent.length > 0) {
      regions.push({ kind: "plain", attrs: {}, content: beforeContent });
    }

    // Find the matching closer (next closer token after this opener)
    let closerIndex = -1;
    for (let j = i + 1; j < tokens.length; j++) {
      const candidate = tokens[j];
      if (candidate !== undefined && candidate.type === "closer") {
        closerIndex = j;
        break;
      }
      // If another opener appears first, the current opener has no closer
      if (candidate !== undefined && candidate.type === "opener") {
        break;
      }
    }

    if (closerIndex >= 0) {
      // Well-formed fence: content between opener end and closer start
      const closer = tokens[closerIndex];
      if (closer !== undefined) {
        const body = markdown.slice(opener.end, closer.index);
        regions.push({ kind: opener.kind, attrs: opener.attrs, content: body });
        cursor = closer.end;
        i = closerIndex + 1;
      }
    } else {
      // Unbalanced opener: content runs to EOF or next opener
      // Find next opener if any
      let nextOpenerIdx = markdown.length;
      for (let j = i + 1; j < tokens.length; j++) {
        const candidate = tokens[j];
        if (candidate !== undefined && candidate.type === "opener") {
          nextOpenerIdx = candidate.index;
          break;
        }
      }
      const body = markdown.slice(opener.end, nextOpenerIdx);
      regions.push({ kind: opener.kind, attrs: opener.attrs, content: body });
      cursor = nextOpenerIdx;
      i++;
    }
  }

  // Trailing plain content after last closer/opener
  if (cursor < markdown.length) {
    const trailing = markdown.slice(cursor);
    if (trailing.length > 0) {
      regions.push({ kind: "plain", attrs: {}, content: trailing });
    }
  }

  return regions;
}
