"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import type { ManifestGroup, ManifestSurface } from "@/server/types";

/** Last path segment — `node:path` is unavailable in a client component. */
function basename(fullPath: string): string {
  return fullPath.split("/").filter((segment) => segment.length > 0).at(-1) ?? fullPath;
}

type DocGroupsNavProps = {
  readonly groups: ManifestGroup[];
  readonly selectedSurfaceId: string | null;
  readonly surfaces: ManifestSurface[];
};

export function DocGroupsNav({ groups, selectedSurfaceId, surfaces }: DocGroupsNavProps) {
  const [query, setQuery] = useState("");
  const normalized = query.trim().toLowerCase();

  const surfaceById = useMemo(
    () => new Map(surfaces.map((surface) => [surface.id, surface])),
    [surfaces]
  );

  function matchesQuery(surface: ManifestSurface): boolean {
    if (normalized === "") {
      return true;
    }
    return (
      surface.title.toLowerCase().includes(normalized) ||
      surface.path.toLowerCase().includes(normalized)
    );
  }

  // Resolve each group to the surfaces that survive the search filter.
  const visibleGroups = groups
    .map((group) => ({
      group,
      surfaces: group.surface_ids
        .map((id) => surfaceById.get(id))
        .filter((surface): surface is ManifestSurface => surface !== undefined)
        .filter(matchesQuery)
    }))
    .filter((entry) => entry.surfaces.length > 0);

  const totalMatches = visibleGroups.reduce((sum, entry) => sum + entry.surfaces.length, 0);

  return (
    <div className="doc-groups-nav">
      <label className="doc-search">
        <span className="doc-search__label">Filter surfaces</span>
        <input
          type="search"
          className="doc-search__input"
          placeholder="Search by title or filename…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </label>

      <p className="doc-search__count muted">
        {totalMatches} surface{totalMatches === 1 ? "" : "s"}
        {normalized === "" ? "" : ` matching “${query.trim()}”`}
      </p>

      {visibleGroups.length === 0 ? (
        <p className="muted">No surfaces match the current filter.</p>
      ) : (
        <ul className="surface-list">
          {visibleGroups.map(({ group, surfaces: groupSurfaces }) => (
            <li className="surface-row" key={group.id}>
              <strong>{group.label}</strong>
              <span className="muted">
                {groupSurfaces.length} surface{groupSurfaces.length === 1 ? "" : "s"}
                {group.transient ? " · transient" : ""}
              </span>
              <ul className="doc-surface-list">
                {groupSurfaces.map((surface) => {
                  const isActive = surface.id === selectedSurfaceId;
                  return (
                    <li key={surface.id}>
                      <Link
                        href={`/documentation?surface=${surface.id}`}
                        className={`doc-surface-link${isActive ? " doc-surface-link--active" : ""}`}
                      >
                        <span className="doc-surface-link__title">{surface.title}</span>
                        <span className="doc-surface-link__path">{basename(surface.path)}</span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
