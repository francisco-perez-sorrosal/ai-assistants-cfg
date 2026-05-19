"use client";

import { useState } from "react";

import { ArtifactCard } from "@/components/artifact-card";
import { Chip } from "@/components/chrome/chip";
import { MetadataChips } from "@/components/metadata-chips";
import { MarkdownSurface } from "@/components/markdown-surface";
import type { AdrRecord } from "./types";

// ─── Filter state helpers ────────────────────────────────────────────────────

function collectFilterValues(records: AdrRecord[], key: string): string[] {
  const seen = new Set<string>();
  for (const record of records) {
    const value = record.data[key];
    if (typeof value === "string" && value.length > 0) {
      seen.add(value);
    } else if (key === "tags" && Array.isArray(value)) {
      for (const tag of value) {
        if (typeof tag === "string") {
          seen.add(tag);
        }
      }
    }
  }
  return Array.from(seen).sort();
}

function recordTags(record: AdrRecord): string[] {
  return Array.isArray(record.data.tags)
    ? (record.data.tags as unknown[]).filter((t): t is string => typeof t === "string")
    : [];
}

function matchesFilter(record: AdrRecord, activeFilters: ActiveFilters): boolean {
  const { status, category, tags } = activeFilters;

  if (status !== null) {
    if (typeof record.data.status !== "string" || record.data.status !== status) {
      return false;
    }
  }

  if (category !== null) {
    if (typeof record.data.category !== "string" || record.data.category !== category) {
      return false;
    }
  }

  if (tags.length > 0) {
    const present = recordTags(record);
    if (!tags.some((tag) => present.includes(tag))) {
      return false;
    }
  }

  return true;
}

// ─── Types ───────────────────────────────────────────────────────────────────

type ActiveFilters = {
  status: string | null;
  category: string | null;
  tags: string[];
};

const EMPTY_FILTERS: ActiveFilters = { status: null, category: null, tags: [] };

// ─── Toggle chip filter row (status / category — short value sets) ────────────

function FilterRow({
  label,
  values,
  active,
  onToggle
}: {
  readonly label: string;
  readonly values: string[];
  readonly active: string | null;
  readonly onToggle: (value: string) => void;
}) {
  if (values.length === 0) {
    return null;
  }

  return (
    <div className="adr-filter-row">
      <span className="adr-filter-label">{label}</span>
      <div className="adr-filter-chips">
        {values.map((value) => (
          <button
            key={value}
            type="button"
            className={`adr-filter-chip${active === value ? " adr-filter-chip--active" : ""}`}
            onClick={() => onToggle(value)}
            aria-pressed={active === value}
          >
            {value}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Tags dropdown (multi-select — collapses a long tag list) ─────────────────

function TagDropdown({
  values,
  selected,
  onToggle
}: {
  readonly values: string[];
  readonly selected: string[];
  readonly onToggle: (value: string) => void;
}) {
  if (values.length === 0) {
    return null;
  }

  return (
    <div className="adr-filter-row">
      <span className="adr-filter-label">Tags</span>
      <details className="adr-tag-dropdown">
        <summary className="adr-tag-dropdown__summary">
          <span>{selected.length > 0 ? `${selected.length} tag${selected.length === 1 ? "" : "s"} selected` : "All tags"}</span>
          <span className="adr-tag-dropdown__chevron" aria-hidden="true" />
        </summary>
        <div className="adr-tag-dropdown__panel">
          {values.map((value) => {
            const isActive = selected.includes(value);
            return (
              <button
                key={value}
                type="button"
                className={`adr-filter-chip${isActive ? " adr-filter-chip--active" : ""}`}
                onClick={() => onToggle(value)}
                aria-pressed={isActive}
              >
                {value}
              </button>
            );
          })}
        </div>
      </details>
    </div>
  );
}

// ─── Main client component ────────────────────────────────────────────────────

export function AdrFilterClient({ records }: { readonly records: AdrRecord[] }) {
  const [filters, setFilters] = useState<ActiveFilters>(EMPTY_FILTERS);

  const allStatuses = collectFilterValues(records, "status");
  const allCategories = collectFilterValues(records, "category");
  const allTags = collectFilterValues(records, "tags");

  const hasFilters = allStatuses.length > 0 || allCategories.length > 0 || allTags.length > 0;

  function toggleSingle(facet: "status" | "category", value: string): void {
    setFilters((prev) => ({
      ...prev,
      [facet]: prev[facet] === value ? null : value
    }));
  }

  function toggleTag(value: string): void {
    setFilters((prev) => ({
      ...prev,
      tags: prev.tags.includes(value)
        ? prev.tags.filter((tag) => tag !== value)
        : [...prev.tags, value]
    }));
  }

  const filtered = records.filter((r) => matchesFilter(r, filters));
  const anyActive =
    filters.status !== null || filters.category !== null || filters.tags.length > 0;

  return (
    <div className="adr-filter-client">
      {hasFilters ? (
        <div className="adr-filters">
          <FilterRow
            label="Status"
            values={allStatuses}
            active={filters.status}
            onToggle={(v) => toggleSingle("status", v)}
          />
          <FilterRow
            label="Category"
            values={allCategories}
            active={filters.category}
            onToggle={(v) => toggleSingle("category", v)}
          />
          <TagDropdown values={allTags} selected={filters.tags} onToggle={toggleTag} />
          {anyActive ? (
            <button
              type="button"
              className="adr-filter-clear"
              onClick={() => setFilters(EMPTY_FILTERS)}
            >
              Clear filters
            </button>
          ) : null}
        </div>
      ) : null}

      <p className="adr-count muted">
        {filtered.length} of {records.length} decision{records.length === 1 ? "" : "s"}
      </p>

      <div className="adr-list">
        {filtered.map((record) => {
          const title =
            typeof record.data.title === "string" ? record.data.title : record.path;
          const adrId =
            typeof record.data.id === "string" ? record.data.id : record.path;
          return (
            <ArtifactCard
              key={record.path}
              title={
                <>
                  <span className="adr-id-badge">{adrId}</span>
                  <span className="adr-card-title">{title}</span>
                </>
              }
              meta={<MetadataChips data={record.data} />}
              footer={
                <Chip variant="neutral" title={record.path}>
                  {record.isDraft ? "draft" : "finalized"}
                </Chip>
              }
            >
              <div id={adrId}>
                <MarkdownSurface body={record.body} />
              </div>
            </ArtifactCard>
          );
        })}
      </div>
    </div>
  );
}
