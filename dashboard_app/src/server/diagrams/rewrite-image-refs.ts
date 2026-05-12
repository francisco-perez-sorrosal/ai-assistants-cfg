import "server-only";

import path from "node:path";

import { ALLOWED_ARTIFACT_ROOTS as ALLOWED_ROOTS } from "@/server/artifacts/project-root";

// Patterns that match image references in Markdown bodies.
// Group 1: the path value for <img src="..."> (double-quoted)
const IMG_TAG_DOUBLE = /<img\s[^>]*src="([^"]+)"[^>]*>/gi;
// Group 1: the path value for <img src='...'> (single-quoted)
const IMG_TAG_SINGLE = /<img\s[^>]*src='([^']+)'[^>]*/gi;
// Group 1: alt text, Group 2: the path value for ![alt](path)
const MD_IMAGE = /!\[([^\]]*)\]\(([^)]+)\)/g;

// URI schemes and prefixes that indicate an already-absolute or external reference.
const EXTERNAL_PREFIXES = ["http://", "https://", "data:", "//", "/"];

function isExternal(ref: string): boolean {
  return EXTERNAL_PREFIXES.some((prefix) => ref.startsWith(prefix));
}

function isInsideAllowlist(projectRelative: string): boolean {
  return ALLOWED_ROOTS.some(
    (root) => projectRelative === root || projectRelative.startsWith(`${root}/`)
  );
}

function resolveProjectRelative(
  imgPath: string,
  sourceDir: string,
  projectRoot: string
): string | null {
  // Resolve the image path relative to the markdown file's directory
  const absoluteImgPath = path.resolve(projectRoot, sourceDir, imgPath);
  const projectRelative = path.relative(projectRoot, absoluteImgPath);

  // Reject if it escapes the project root or isn't in the allowlist
  if (projectRelative.startsWith("..") || path.isAbsolute(projectRelative)) {
    return null;
  }

  if (!isInsideAllowlist(projectRelative)) {
    return null;
  }

  return projectRelative;
}

/**
 * Rewrites relative <img src="...">, <img src='...'>, and ![alt](path) references
 * in a Markdown body so they point to /api/diagram?path=<project-relative-path>.
 *
 * Only references whose resolved target is inside the project-root allowlist
 * (.ai-state/, .ai-work/, docs/, ROADMAP.md) are rewritten.
 * Absolute paths, http(s)://, data:, and // are left untouched.
 * References that resolve outside the allowlist are left as-is (broken image, not a crash).
 *
 * @param markdown  The raw Markdown body to process
 * @param sourceDir Directory of the source file, relative to projectRoot
 *                  (e.g. ".ai-state" for DESIGN.md, "docs" for architecture.md)
 * @param projectRoot Absolute path to the Praxion project root
 */
export function rewriteRelativeImageRefs(
  markdown: string,
  sourceDir: string,
  projectRoot: string
): string {
  let result = markdown;

  // Rewrite <img src="...">
  result = result.replace(IMG_TAG_DOUBLE, (match, imgSrc: string) => {
    if (isExternal(imgSrc)) return match;
    const projectRelative = resolveProjectRelative(imgSrc, sourceDir, projectRoot);
    if (projectRelative === null) return match;
    return match.replace(`"${imgSrc}"`, `"/api/diagram?path=${encodeURIComponent(projectRelative)}"`);
  });

  // Rewrite <img src='...'>
  result = result.replace(IMG_TAG_SINGLE, (match, imgSrc: string) => {
    if (isExternal(imgSrc)) return match;
    const projectRelative = resolveProjectRelative(imgSrc, sourceDir, projectRoot);
    if (projectRelative === null) return match;
    return match.replace(`'${imgSrc}'`, `'/api/diagram?path=${encodeURIComponent(projectRelative)}'`);
  });

  // Rewrite ![alt](path)
  result = result.replace(MD_IMAGE, (match, alt: string, imgSrc: string) => {
    if (isExternal(imgSrc)) return match;
    const projectRelative = resolveProjectRelative(imgSrc, sourceDir, projectRoot);
    if (projectRelative === null) return match;
    return `![${alt}](/api/diagram?path=${encodeURIComponent(projectRelative)})`;
  });

  return result;
}
