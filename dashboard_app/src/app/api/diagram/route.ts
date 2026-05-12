import "server-only";

import { promises as fs } from "node:fs";
import path from "node:path";

import { NextResponse } from "next/server";

import { getConfig } from "@/lib/config";
import { assertAllowedArtifactPath } from "@/server/artifacts/project-root";

// Note: bytes served here as <img src="/api/diagram?path=..."> are opaque to the page.
// An SVG loaded via <img src> cannot execute script in modern browsers regardless of
// its content — XSS via <img>-served SVG is not a real vector. Therefore, the raw file
// bytes are served without sanitization. Only inline-injected SVG (via DiagramViewer's
// dangerouslySetInnerHTML) requires sanitization — see server/diagrams/sanitize.ts.

const SVG_EXTENSION = ".svg";

export async function GET(request: Request): Promise<NextResponse> {
  const url = new URL(request.url);
  const filePath = url.searchParams.get("path");

  if (!filePath || filePath.trim() === "") {
    return NextResponse.json({ error: "path is required" }, { status: 400 });
  }

  // Defense in depth: only serve .svg files regardless of allowlist membership.
  if (!filePath.toLowerCase().endsWith(SVG_EXTENSION)) {
    return NextResponse.json({ error: "only .svg files served" }, { status: 403 });
  }

  let config: ReturnType<typeof getConfig>;
  try {
    config = getConfig();
  } catch {
    return NextResponse.json({ error: "server configuration error" }, { status: 500 });
  }

  const absolutePath = path.join(config.projectRoot, filePath);

  try {
    await assertAllowedArtifactPath(config.projectRoot, absolutePath);
  } catch {
    return NextResponse.json({ error: "path not permitted" }, { status: 403 });
  }

  let content: string;
  try {
    content = await fs.readFile(absolutePath, "utf-8");
  } catch {
    return NextResponse.json({ error: "not found" }, { status: 404 });
  }

  return new NextResponse(content, {
    headers: {
      "Content-Type": "image/svg+xml",
      "Cache-Control": "no-store"
    }
  });
}
