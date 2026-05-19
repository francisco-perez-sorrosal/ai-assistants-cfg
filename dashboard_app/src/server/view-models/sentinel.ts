import "server-only";

import path from "node:path";

import { isSentinelReport, listDirectory } from "@/server/artifacts/files";
import { assertAllowedArtifactPath, validateProjectRoot } from "@/server/artifacts/project-root";
import { readMarkdown } from "@/server/parsers/content";
import { extractSections, parseSentinelLog } from "@/server/sentinel/extract-sections";
import type { SentinelLogPoint, SentinelSections } from "@/server/sentinel/extract-sections";

export type { SentinelLogPoint, SentinelSections };

/**
 * One fully-loaded sentinel report: its body, parsed finding sections, and the
 * matching `SENTINEL_LOG.md` row (grade + finding counts) when one exists.
 */
export type SentinelReport = {
  body: string;
  data: Record<string, unknown>;
  fileName: string;
  highlight: SentinelLogPoint | null;
  path: string;
  sections: SentinelSections;
};

export type SentinelData = {
  log: { body: string } | null;
  logSeries: SentinelLogPoint[];
  reports: SentinelReport[];
};

export async function getSentinelData(projectRoot: string): Promise<SentinelData> {
  const validatedRoot = await validateProjectRoot(projectRoot);
  const reportsRoot = path.join(validatedRoot, ".ai-state", "sentinel_reports");

  // Newest-first: filenames sort lexically because the timestamp is fixed-width.
  const reportFileNames = (await listDirectory(reportsRoot))
    .filter((entry) => isSentinelReport(entry))
    .sort((left, right) => right.localeCompare(left));

  const log = await readMarkdown(
    await assertAllowedArtifactPath(validatedRoot, path.join(reportsRoot, "SENTINEL_LOG.md"))
  );
  const logSeries = parseSentinelLog(log?.body ?? "");
  const highlightByFile = new Map<string, SentinelLogPoint>();
  for (const point of logSeries) {
    if (point.reportFile !== null) {
      highlightByFile.set(point.reportFile, point);
    }
  }

  const reports = (
    await Promise.all(
      reportFileNames.map(async (fileName) => {
        const file = await readMarkdown(
          await assertAllowedArtifactPath(validatedRoot, path.join(reportsRoot, fileName))
        );
        if (file === null) {
          return null;
        }
        return {
          body: file.body,
          data: file.data,
          fileName,
          highlight: highlightByFile.get(fileName) ?? null,
          path: file.path,
          sections: extractSections(file.body)
        } satisfies SentinelReport;
      })
    )
  ).filter((report): report is SentinelReport => report !== null);

  return {
    log: log ? { body: log.body } : null,
    logSeries,
    reports
  };
}
