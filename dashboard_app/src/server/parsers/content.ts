import "server-only";

import matter from "gray-matter";
import YAML from "yaml";

import { readText } from "@/server/artifacts/files";
import type { MarkdownFile } from "@/server/types";

/**
 * Strips the leading YAML frontmatter block from raw markdown text so the
 * body can still be rendered when frontmatter parsing fails.  Returns the
 * full text unchanged when no frontmatter delimiter is found.
 */
function stripFrontmatterBlock(text: string): string {
  if (!text.startsWith("---")) {
    return text;
  }
  const closeIdx = text.indexOf("\n---", 3);
  if (closeIdx === -1) {
    return text;
  }
  return text.slice(closeIdx + 4).replace(/^\n/, "");
}

export async function readMarkdown(target: string): Promise<MarkdownFile | null> {
  const text = await readText(target);
  if (text === null) {
    return null;
  }

  try {
    const parsed = matter(text);
    return {
      body: parsed.content,
      data: parsed.data as Record<string, unknown>,
      path: target
    };
  } catch (err) {
    console.warn(
      `[dashboard] readMarkdown: frontmatter parse failed for "${target}" — falling back to empty data.`,
      err instanceof Error ? err.message : String(err)
    );
    return {
      body: stripFrontmatterBlock(text),
      data: {},
      path: target
    };
  }
}

export async function readJson<T>(target: string): Promise<T | null> {
  const text = await readText(target);
  if (text === null) {
    return null;
  }

  try {
    return JSON.parse(text) as T;
  } catch {
    return null;
  }
}

export async function readYaml<T>(target: string): Promise<T | null> {
  const text = await readText(target);
  if (text === null) {
    return null;
  }

  try {
    return YAML.parse(text) as T;
  } catch {
    return null;
  }
}
