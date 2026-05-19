"use client";

import { useMemo, useState } from "react";

import { ArtifactCard } from "@/components/artifact-card";
import { Chip } from "@/components/chrome/chip";
import type { ChipVariant } from "@/components/chrome/chip";
import { MarkdownSurface } from "@/components/markdown-surface";
import type { SentinelReport } from "@/server/view-models/sentinel";

// ─── Formatting helpers ───────────────────────────────────────────────────────

const REPORT_TIMESTAMP_PATTERN =
  /SENTINEL_REPORT_(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})/;

/** Recovers a Date from a `SENTINEL_REPORT_YYYY-MM-DD_HH-MM-SS.md` filename. */
function parseReportTimestamp(fileName: string): Date | null {
  const match = REPORT_TIMESTAMP_PATTERN.exec(fileName);
  if (!match) {
    return null;
  }
  const [, year, month, day, hour, minute, second] = match;
  const date = new Date(`${year}-${month}-${day}T${hour}:${minute}:${second}Z`);
  return Number.isNaN(date.getTime()) ? null : date;
}

function formatReportLabel(fileName: string): string {
  const date = parseReportTimestamp(fileName);
  if (date === null) {
    return fileName;
  }
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC"
  }).format(date);
}

const GRADE_VARIANTS: Record<string, ChipVariant> = {
  a: "grade-a",
  b: "grade-b",
  c: "grade-c",
  d: "grade-d"
};

function gradeVariant(grade: string | null): ChipVariant {
  return grade ? GRADE_VARIANTS[grade.toLowerCase()] ?? "neutral" : "neutral";
}

// ─── Header strip ─────────────────────────────────────────────────────────────

type FindingCount = {
  className: string;
  label: string;
  value: number | null;
};

function findingCounts(report: SentinelReport): FindingCount[] {
  const highlight = report.highlight;
  return [
    {
      className: (highlight?.critical ?? 0) > 0 ? "sentinel-strip__count--bad" : "",
      label: "Critical",
      value: highlight?.critical ?? null
    },
    {
      className: (highlight?.important ?? 0) > 0 ? "sentinel-strip__count--warn" : "",
      label: "Important",
      value: highlight?.important ?? null
    },
    {
      className: "",
      label: "Suggested",
      value: highlight?.suggested ?? null
    }
  ];
}

function HeaderStrip({
  report,
  reports,
  onSelect
}: {
  readonly onSelect: (fileName: string) => void;
  readonly report: SentinelReport;
  readonly reports: SentinelReport[];
}) {
  const highlight = report.highlight;
  const counts = findingCounts(report);

  return (
    <section className="sentinel-strip" aria-label="Sentinel report summary">
      <div className="sentinel-strip__highlights">
        <span className="sentinel-strip__date">{formatReportLabel(report.fileName)}</span>
        <Chip variant={gradeVariant(highlight?.grade ?? null)}>
          Health {highlight?.grade?.toUpperCase() ?? "—"}
        </Chip>
        <Chip variant={gradeVariant(highlight?.coherence ?? null)}>
          Coherence {highlight?.coherence?.toUpperCase() ?? "—"}
        </Chip>
        <ul className="sentinel-strip__counts">
          {counts.map((count) => (
            <li key={count.label} className={`sentinel-strip__count ${count.className}`}>
              <span className="sentinel-strip__count-value">{count.value ?? "—"}</span>
              <span className="sentinel-strip__count-label">{count.label}</span>
            </li>
          ))}
        </ul>
      </div>

      <label className="sentinel-strip__selector">
        <span className="sentinel-strip__selector-label">Report</span>
        <select
          aria-label="Select sentinel report by date"
          value={report.fileName}
          onChange={(event) => onSelect(event.target.value)}
        >
          {reports.map((candidate) => (
            <option key={candidate.fileName} value={candidate.fileName}>
              {formatReportLabel(candidate.fileName)}
            </option>
          ))}
        </select>
      </label>
    </section>
  );
}

// ─── Main client component ────────────────────────────────────────────────────

export function SentinelClient({ reports }: { readonly reports: SentinelReport[] }) {
  const [selectedFileName, setSelectedFileName] = useState(reports[0]?.fileName ?? "");

  const selected = useMemo(
    () => reports.find((report) => report.fileName === selectedFileName) ?? reports[0] ?? null,
    [reports, selectedFileName]
  );

  if (selected === null) {
    return null;
  }

  const { sections } = selected;

  return (
    <div className="sentinel-client">
      <HeaderStrip report={selected} reports={reports} onSelect={setSelectedFileName} />

      <div className="sentinel-sections">
        {sections.critical.trim().length > 0 ? (
          <ArtifactCard title="Critical" defaultOpen={true}>
            <MarkdownSurface body={sections.critical} />
          </ArtifactCard>
        ) : null}

        {sections.important.trim().length > 0 ? (
          <ArtifactCard title="Important">
            <MarkdownSurface body={sections.important} />
          </ArtifactCard>
        ) : null}

        {sections.suggested.trim().length > 0 ? (
          <ArtifactCard title="Suggested">
            <MarkdownSurface body={sections.suggested} />
          </ArtifactCard>
        ) : null}

        {sections.rest.trim().length > 0 ? (
          <ArtifactCard title="Full report" defaultOpen={sections.critical.trim().length === 0}>
            <MarkdownSurface body={sections.rest} />
          </ArtifactCard>
        ) : null}
      </div>
    </div>
  );
}
