import { Chip } from "@/components/chrome/chip";
import type { ChipVariant } from "@/components/chrome/chip";

const STATUS_VARIANTS: Record<string, ChipVariant> = {
  accepted: "status-accepted",
  proposed: "status-proposed",
  "re-affirmation": "status-reaffirmation",
  superseded: "status-superseded"
};

const GRADE_VARIANTS: Record<string, ChipVariant> = {
  a: "grade-a",
  b: "grade-b",
  c: "grade-c",
  d: "grade-d"
};

function statusVariant(value: string): ChipVariant {
  return STATUS_VARIANTS[value.toLowerCase()] ?? "neutral";
}

function gradeVariant(value: string): ChipVariant {
  return GRADE_VARIANTS[value.toLowerCase()] ?? "neutral";
}

function renderKnownKey(key: string, value: unknown): React.ReactNode[] {
  if (key === "status" && typeof value === "string") {
    return [
      <Chip key={`status-${value}`} variant={statusVariant(value)}>
        {value}
      </Chip>
    ];
  }

  if (key === "grade" && typeof value === "string") {
    return [
      <Chip key={`grade-${value}`} variant={gradeVariant(value)}>
        Grade {value.toUpperCase()}
      </Chip>
    ];
  }

  if (key === "tags" && Array.isArray(value)) {
    return value.filter((tag): tag is string => typeof tag === "string").map((tag) => (
      <Chip key={`tag-${tag}`} variant="neutral">
        {tag}
      </Chip>
    ));
  }

  if ((key === "category" || key === "date" || key === "pipeline_tier" || key === "made_by") && typeof value === "string") {
    return [
      <Chip key={`${key}-${value}`} variant="neutral">
        {value}
      </Chip>
    ];
  }

  if (key === "summary" && typeof value === "string") {
    return [
      <span key="summary" className="metadata-chips__summary">
        {value}
      </span>
    ];
  }

  return [];
}

const KNOWN_KEYS = new Set(["status", "grade", "tags", "category", "date", "pipeline_tier", "made_by", "summary"]);

export function MetadataChips({ data }: { data: Record<string, unknown> }) {
  const chips: React.ReactNode[] = [];

  for (const [key, value] of Object.entries(data)) {
    if (!KNOWN_KEYS.has(key)) {
      continue;
    }
    chips.push(...renderKnownKey(key, value));
  }

  if (chips.length === 0) {
    return null;
  }

  return <div className="metadata-chips">{chips}</div>;
}
