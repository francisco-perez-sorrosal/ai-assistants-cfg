import "server-only";

import path from "node:path";

import {
  CANONICAL_WORKSHOP_ARTIFACTS,
  listDirectoryByMtimeDesc,
  readText
} from "@/server/artifacts/files";
import { assertAllowedArtifactPath, validateProjectRoot } from "@/server/artifacts/project-root";
import { readMarkdown } from "@/server/parsers/content";
import { parseProgressBody, parseWipBody } from "@/server/parsers/workshops";
import type { WorkshopArtifact, WorkshopState } from "@/server/types";

/** Markdown artifacts render through MarkdownSurface; everything else as code. */
function renderModeFor(name: string): WorkshopArtifact["renderMode"] {
  return /\.(md|markdown)$/i.test(name) ? "markdown" : "code";
}

export async function getWorkshopsData(projectRoot: string): Promise<WorkshopState[]> {
  const validatedRoot = await validateProjectRoot(projectRoot);
  const workshopsRoot = path.join(validatedRoot, ".ai-work");
  const workshopDirs = await listDirectoryByMtimeDesc(workshopsRoot);

  return Promise.all(
    workshopDirs.map(async (dirName) => {
      const workshopRoot = path.join(workshopsRoot, dirName);
      const [wipPath, progressPath] = await Promise.all([
        assertAllowedArtifactPath(validatedRoot, path.join(workshopRoot, "WIP.md")),
        assertAllowedArtifactPath(validatedRoot, path.join(workshopRoot, "PROGRESS.md"))
      ]);
      const [wip, progress] = await Promise.all([
        readMarkdown(wipPath),
        readMarkdown(progressPath)
      ]);

      const wipState = wip
        ? parseWipBody(wip.body)
        : { currentStep: null, progress: [], status: null };
      const events = progress ? parseProgressBody(progress.body) : [];

      // Read each canonical artifact's content so it can be viewed inline.
      const artifacts = (
        await Promise.all(
          CANONICAL_WORKSHOP_ARTIFACTS.map(
            async (name): Promise<WorkshopArtifact | null> => {
              const artifactPath = await assertAllowedArtifactPath(
                validatedRoot,
                path.join(workshopRoot, name)
              );
              const body = await readText(artifactPath);
              if (body === null) {
                return null;
              }
              return { body, name, renderMode: renderModeFor(name) };
            }
          )
        )
      ).filter((artifact): artifact is WorkshopArtifact => artifact !== null);

      return {
        artifacts,
        currentStep: wipState.currentStep,
        events,
        path: workshopRoot,
        progress: wipState.progress,
        status: wipState.status
      };
    })
  );
}
