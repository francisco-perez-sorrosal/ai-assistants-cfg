"""MemoryStore: CRUD operations and file I/O for persistent memory."""

from __future__ import annotations

import contextlib
import fcntl
import json
import math
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from memory_mcp.lifecycle import analyze as lifecycle_analyze
from memory_mcp.schema import (
    DEFAULT_IMPORTANCE,
    MAX_IMPORTANCE,
    MIN_IMPORTANCE,
    SCHEMA_VERSION,
    VALID_CATEGORIES,
    VALID_RELATIONS,
    MemoryEntry,
    Source,
    migrate_v1_0_to_v1_1,
    migrate_v1_1_to_v1_2,
)

# -- Constants ----------------------------------------------------------------

JSON_INDENT = 2
BACKUP_SUFFIX = ".backup.json"
PRE_MIGRATION_SUFFIX = ".pre-migration-1.0.json"

# Auto-link constants
AUTO_LINK_TAG_OVERLAP_THRESHOLD = 2
MAX_AUTO_LINKS_PER_REMEMBER = 3
AUTO_LINK_RELATION = "related-to"

PRE_MIGRATION_V1_1_SUFFIX = ".pre-migration-1.1.json"

# Dedup thresholds
MIN_TAG_OVERLAP_FOR_CANDIDATE = 2
STRONG_TAG_OVERLAP_THRESHOLD = 3
MIN_WORD_LENGTH = 3
HIGH_VALUE_SIMILARITY_RATIO = 0.6
MIN_SIGNIFICANT_WORDS_FOR_VALUE_MATCH = 3
STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "and", "but", "or", "not",
    "no", "so", "if", "for", "to", "of", "in", "on", "at", "by", "with",
    "from", "as", "into", "that", "this", "it", "its",
})

# Search ranking weights (each signal normalized to 0.0-1.0)
SEARCH_WEIGHTS = {
    "text_match": 0.4,
    "tag_match": 0.2,
    "importance": 0.25,
    "recency": 0.15,
}

# Recency exponential decay: half-life ~21 days (score ~0.37 at 30 days)
RECENCY_DECAY_DAYS = 30


# -- Helpers ------------------------------------------------------------------


def _now_utc() -> str:
    """ISO 8601 UTC timestamp with Z suffix."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _clamp_importance(value: int) -> int:
    return max(MIN_IMPORTANCE, min(MAX_IMPORTANCE, value))


def _human_file_size(byte_count: int) -> str:
    """Format byte count as human-readable string."""
    if byte_count < 1024:
        return f"{byte_count} B"
    kib = byte_count / 1024
    if kib < 1024:
        return f"{kib:.1f} KB"
    mib = kib / 1024
    return f"{mib:.1f} MB"


# -- Dedup helpers ------------------------------------------------------------


def _extract_significant_words(text: str) -> set[str]:
    """Extract significant words from text, filtering stopwords and short tokens."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if len(w) >= MIN_WORD_LENGTH and w not in STOP_WORDS}


def _tag_overlap_count(tags_a: list[str], tags_b: list[str]) -> int:
    """Count shared tags between two tag lists (case-insensitive)."""
    set_a = {t.lower() for t in tags_a}
    set_b = {t.lower() for t in tags_b}
    return len(set_a & set_b)


def _value_similarity_ratio(new_words: set[str], existing_words: set[str]) -> float:
    """Fraction of new_words that appear in existing_words. Returns 0.0 if no words."""
    if not new_words:
        return 0.0
    return len(new_words & existing_words) / len(new_words)


def _find_dedup_candidates(
    new_key: str,
    new_value: str,
    new_tags: list[str],
    entries: dict[str, dict],
    category: str,
) -> list[dict]:
    """Scan entries for overlap with the proposed new entry.

    Returns a list of candidate dicts with match_reason and overlap details.
    Skips the entry whose key matches new_key (exact key match is handled separately).
    """
    new_words = _extract_significant_words(new_value)
    candidates = []

    for existing_key, entry in entries.items():
        if existing_key == new_key:
            continue

        reasons = []
        existing_tags = entry.get("tags", [])
        tag_overlap = _tag_overlap_count(new_tags, existing_tags)
        if tag_overlap >= MIN_TAG_OVERLAP_FOR_CANDIDATE:
            reasons.append(f"tag_overlap({tag_overlap})")

        existing_words = _extract_significant_words(entry.get("value", ""))
        similarity = _value_similarity_ratio(new_words, existing_words)
        has_enough_words = len(new_words) >= MIN_SIGNIFICANT_WORDS_FOR_VALUE_MATCH
        if has_enough_words and similarity >= HIGH_VALUE_SIMILARITY_RATIO:
            reasons.append(f"value_similarity({similarity:.0%})")

        if reasons:
            candidates.append({
                "category": category,
                "key": existing_key,
                "value": entry.get("value", ""),
                "tags": existing_tags,
                "match_reason": ", ".join(reasons),
                "tag_overlap": tag_overlap,
                "value_similarity": round(similarity, 2),
            })

    return candidates


def _recommend_action(candidates: list[dict], new_value: str) -> str:
    """Choose ADD, UPDATE, or NOOP recommendation based on candidate overlap."""
    new_words = _extract_significant_words(new_value)

    for candidate in candidates:
        existing_words = _extract_significant_words(candidate["value"])
        has_substance = len(new_words) >= MIN_SIGNIFICANT_WORDS_FOR_VALUE_MATCH
        if has_substance and new_words == existing_words:
            return "NOOP"

    for candidate in candidates:
        if candidate["tag_overlap"] >= STRONG_TAG_OVERLAP_THRESHOLD:
            return "UPDATE"
        if candidate["value_similarity"] >= HIGH_VALUE_SIMILARITY_RATIO:
            return "UPDATE"

    return "ADD"


# -- Search scoring helpers ----------------------------------------------------


def _compute_text_match_score(
    key: str, entry: dict, query_lower: str,
) -> float:
    """Score text match: 1.0 for exact key, 0.7 for key substring, 0.5 for value/tag match."""
    if key.lower() == query_lower:
        return 1.0
    if query_lower in key.lower():
        return 0.7
    if query_lower in entry.get("value", "").lower():
        return 0.5
    tags = entry.get("tags", [])
    if any(query_lower in tag.lower() for tag in tags):
        return 0.5
    return 0.0


def _compute_tag_match_score(entry: dict, query_terms: list[str]) -> float:
    """Fraction of entry tags that match any query term."""
    if not query_terms:
        return 0.0
    tags_lower = {t.lower() for t in entry.get("tags", [])}
    if not tags_lower:
        return 0.0
    matching = sum(
        1 for term in query_terms if any(term in tag for tag in tags_lower)
    )
    return min(matching / max(len(query_terms), 1), 1.0)


def _compute_importance_score(entry: dict) -> float:
    """Normalize importance from 1-10 scale to 0.0-1.0."""
    importance = entry.get("importance", DEFAULT_IMPORTANCE)
    return importance / MAX_IMPORTANCE


def _compute_recency_score(entry: dict, now: datetime) -> float:
    """Exponential decay based on last_accessed. 0.0 if never accessed."""
    last_accessed = entry.get("last_accessed")
    if not last_accessed:
        return 0.0
    accessed_str = last_accessed.replace("Z", "+00:00")
    accessed_dt = datetime.fromisoformat(accessed_str)
    days_since = (now - accessed_dt).total_seconds() / 86400
    return math.exp(-days_since / RECENCY_DECAY_DAYS)


def _compute_search_score(signals: dict[str, float]) -> float:
    """Weighted combination of individual signal scores."""
    return sum(
        SEARCH_WEIGHTS[signal] * score for signal, score in signals.items()
    )


# -- MemoryStore --------------------------------------------------------------


class MemoryStore:
    """Persistent memory store backed by a single JSON file.

    Provides CRUD operations, access tracking, atomic writes, link management,
    and chained auto-migration (v1.0 -> v1.1 -> v1.2) on first load.
    """

    def __init__(self, file_path: Path) -> None:
        self._path = Path(file_path)
        self._ensure_file_exists()
        self._auto_migrate_if_needed()

    # -- File I/O (private) ---------------------------------------------------

    def _ensure_file_exists(self) -> None:
        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            empty_doc = {
                "schema_version": SCHEMA_VERSION,
                "session_count": 0,
                "memories": {cat: {} for cat in VALID_CATEGORIES},
            }
            self._save(empty_doc)

    def _load(self) -> dict:
        """Read and validate the JSON memory file."""
        text = self._path.read_text(encoding="utf-8")
        data = json.loads(text)
        if "schema_version" not in data:
            msg = f"Missing 'schema_version' in {self._path}"
            raise ValueError(msg)
        if "memories" not in data:
            msg = f"Missing 'memories' in {self._path}"
            raise ValueError(msg)
        return data

    def _save(self, data: dict) -> None:
        """Atomic write: temp file in same directory, then os.replace()."""
        content = json.dumps(data, indent=JSON_INDENT, ensure_ascii=False) + "\n"
        fd, tmp_path = tempfile.mkstemp(
            dir=self._path.parent,
            prefix=".memory_tmp_",
            suffix=".json",
        )
        try:
            os.write(fd, content.encode("utf-8"))
            os.close(fd)
            os.replace(tmp_path, self._path)
        except BaseException:
            os.close(fd) if not _is_fd_closed(fd) else None
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
            raise

    @contextlib.contextmanager
    def _lock(self):
        """Exclusive file lock for read-modify-write safety."""
        lock_path = self._path.with_suffix(".lock")
        lock_path.touch(exist_ok=True)
        lock_fd = lock_path.open("w")
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()

    def _auto_migrate_if_needed(self) -> None:
        """Detect outdated schema and apply chained migrations (v1.0 -> v1.1 -> v1.2)."""
        data = self._load()
        version = data.get("schema_version")

        if version == SCHEMA_VERSION:
            return

        if version == "1.0":
            backup_path = self._path.with_name(
                self._path.stem + PRE_MIGRATION_SUFFIX
            )
            backup_content = json.dumps(data, indent=JSON_INDENT, ensure_ascii=False) + "\n"
            backup_path.write_text(backup_content, encoding="utf-8")
            data = migrate_v1_0_to_v1_1(data)
            version = "1.1"

        if version == "1.1":
            backup_path = self._path.with_name(
                self._path.stem + PRE_MIGRATION_V1_1_SUFFIX
            )
            backup_content = json.dumps(data, indent=JSON_INDENT, ensure_ascii=False) + "\n"
            backup_path.write_text(backup_content, encoding="utf-8")
            data = migrate_v1_1_to_v1_2(data)

        self._save(data)

    def _read_modify_write(self, mutator):
        """Lock, load, apply mutator, save. Returns mutator's return value."""
        with self._lock():
            data = self._load()
            result = mutator(data)
            self._save(data)
            return result

    # -- Validation helpers ---------------------------------------------------

    @staticmethod
    def _validate_category(category: str) -> None:
        if category not in VALID_CATEGORIES:
            msg = f"Invalid category '{category}'. Must be one of: {', '.join(VALID_CATEGORIES)}"
            raise ValueError(msg)

    # -- Public API -----------------------------------------------------------

    def session_start(self) -> dict:
        """Increment session_count and return full memory summary."""

        def _mutate(data: dict) -> dict:
            data["session_count"] = data.get("session_count", 0) + 1
            memories = data.get("memories", {})
            categories = {}
            total = 0
            for cat_name in VALID_CATEGORIES:
                count = len(memories.get(cat_name, {}))
                categories[cat_name] = count
                total += count
            return {
                "session_count": data["session_count"],
                "categories": categories,
                "total": total,
                "schema_version": data.get("schema_version", SCHEMA_VERSION),
            }

        return self._read_modify_write(_mutate)

    def remember(
        self,
        category: str,
        key: str,
        value: str,
        *,
        tags: list[str] | None = None,
        importance: int = 5,
        source_type: str = "session",
        confidence: float | None = None,
        force: bool = False,
        broad: bool = False,
    ) -> dict:
        """Create or update a memory entry.

        When the key already exists, updates in place (no dedup check).
        For new keys, scans for overlapping entries and returns candidates
        unless ``force=True`` bypasses the check.
        Set ``broad=True`` to search across all categories instead of just
        the target category.
        """
        self._validate_category(category)
        importance = _clamp_importance(importance)
        resolved_tags = sorted(tags) if tags else []

        if not force:
            candidates = self._find_candidates(
                category, key, value, resolved_tags, broad=broad
            )
            if candidates:
                recommendation = _recommend_action(candidates, value)
                return {
                    "action": "candidates",
                    "candidates": candidates,
                    "recommendation": recommendation,
                }

        return self._do_remember(
            category, key, value,
            tags=resolved_tags,
            importance=importance,
            source_type=source_type,
            confidence=confidence,
        )

    def _find_candidates(
        self,
        category: str,
        key: str,
        value: str,
        tags: list[str],
        *,
        broad: bool = False,
    ) -> list[dict]:
        """Scan for dedup candidates (read-only, no file mutation)."""
        data = self._load()
        memories = data.get("memories", {})

        # Check if exact key exists -- skip dedup entirely
        cat_entries = memories.get(category, {})
        if key in cat_entries:
            return []

        all_candidates: list[dict] = []
        if broad:
            for cat_name in VALID_CATEGORIES:
                entries = memories.get(cat_name, {})
                all_candidates.extend(
                    _find_dedup_candidates(key, value, tags, entries, cat_name)
                )
        else:
            all_candidates = _find_dedup_candidates(
                key, value, tags, cat_entries, category
            )

        return all_candidates

    def _do_remember(
        self,
        category: str,
        key: str,
        value: str,
        *,
        tags: list[str],
        importance: int,
        source_type: str,
        confidence: float | None,
    ) -> dict:
        """Unconditionally create or update a memory entry (no dedup check).

        For new entries (ADD), scans the same category for tag-matched entries
        and auto-creates ``related-to`` links when 2+ tags overlap.
        """
        now = _now_utc()

        def _mutate(data: dict) -> dict:
            memories = data.setdefault("memories", {})
            cat_entries = memories.setdefault(category, {})

            if key in cat_entries:
                existing = cat_entries[key]
                existing["value"] = value
                existing["updated_at"] = now
                if tags:
                    merged = list(set(existing.get("tags", [])) | set(tags))
                    existing["tags"] = sorted(merged)
                existing["importance"] = importance
                if confidence is not None:
                    existing["confidence"] = confidence
                return {"action": "UPDATE", "entry": dict(existing)}

            entry = MemoryEntry(
                value=value,
                created_at=now,
                updated_at=now,
                tags=list(tags),
                confidence=confidence,
                importance=importance,
                source=Source(type=source_type),
                access_count=0,
                last_accessed=None,
                status="active",
            )
            entry_dict = entry.to_dict()
            cat_entries[key] = entry_dict

            # Auto-link: find tag-matched entries in the same category
            auto_links = _find_auto_links(category, key, tags, cat_entries)
            if auto_links:
                entry_dict["links"] = auto_links

            return {"action": "ADD", "entry": dict(entry_dict)}

        return self._read_modify_write(_mutate)

    def forget(self, category: str, key: str) -> dict:
        """Remove a memory entry, clean up incoming links, and create a backup."""
        self._validate_category(category)
        target_ref = f"{category}.{key}"

        def _mutate(data: dict) -> dict:
            memories = data.get("memories", {})
            cat_entries = memories.get(category, {})
            if key not in cat_entries:
                msg = f"Key '{key}' not found in category '{category}'"
                raise KeyError(msg)

            removed = cat_entries.pop(key)

            # Clean up incoming links from all entries pointing to the deleted entry
            _remove_incoming_links(memories, target_ref)

            backup_path = self._path.with_name(self._path.stem + BACKUP_SUFFIX)
            backup_content = json.dumps(data, indent=JSON_INDENT, ensure_ascii=False) + "\n"
            backup_path.write_text(backup_content, encoding="utf-8")

            return {"removed": removed, "backup_path": str(backup_path)}

        return self._read_modify_write(_mutate)

    def recall(self, category: str, key: str | None = None) -> dict:
        """Retrieve entries with access tracking."""
        self._validate_category(category)
        now = _now_utc()

        def _mutate(data: dict) -> dict:
            memories = data.get("memories", {})
            cat_entries = memories.get(category, {})

            if key is not None:
                if key not in cat_entries:
                    msg = f"Key '{key}' not found in category '{category}'"
                    raise KeyError(msg)
                entry = cat_entries[key]
                entry["access_count"] = entry.get("access_count", 0) + 1
                entry["last_accessed"] = now
                return {"entries": {key: dict(entry)}}

            for entry in cat_entries.values():
                entry["access_count"] = entry.get("access_count", 0) + 1
                entry["last_accessed"] = now
            return {"entries": {k: dict(v) for k, v in cat_entries.items()}}

        return self._read_modify_write(_mutate)

    def search(self, query: str, category: str | None = None) -> dict:
        """Multi-signal ranked search across keys, values, and tags.

        Entries must match the text query to be included. Among matches,
        results are ranked by a weighted combination of text match quality,
        tag overlap, importance, and recency signals.
        """
        if category is not None:
            self._validate_category(category)
        now_str = _now_utc()
        now_dt = datetime.now(UTC)
        query_lower = query.lower()
        query_terms = [t for t in query_lower.split() if t]

        def _mutate(data: dict) -> dict:
            memories = data.get("memories", {})
            categories_to_search = (
                {category: memories.get(category, {})}
                if category
                else memories
            )

            results = []
            for cat_name, entries in categories_to_search.items():
                for entry_key, entry in entries.items():
                    match_reasons = _find_match_reasons(
                        entry_key, entry, query_lower
                    )
                    if not match_reasons:
                        continue

                    # Compute signals BEFORE updating access tracking
                    # so recency reflects the entry's pre-search state
                    signals = {
                        "text_match": _compute_text_match_score(
                            entry_key, entry, query_lower,
                        ),
                        "tag_match": _compute_tag_match_score(
                            entry, query_terms,
                        ),
                        "importance": _compute_importance_score(entry),
                        "recency": _compute_recency_score(entry, now_dt),
                    }
                    score = _compute_search_score(signals)

                    # Track access after scoring
                    entry["access_count"] = entry.get("access_count", 0) + 1
                    entry["last_accessed"] = now_str

                    results.append({
                        "category": cat_name,
                        "key": entry_key,
                        "entry": dict(entry),
                        "score": round(score, 4),
                        "signals": {k: round(v, 4) for k, v in signals.items()},
                        "match_reason": ", ".join(match_reasons),
                    })

            results.sort(key=lambda r: r["score"], reverse=True)
            return {"results": results}

        return self._read_modify_write(_mutate)

    def status(self) -> dict:
        """Return store status with category counts and metadata."""
        data = self._load()
        memories = data.get("memories", {})
        categories = {}
        total = 0
        for cat_name in VALID_CATEGORIES:
            count = len(memories.get(cat_name, {}))
            categories[cat_name] = count
            total += count

        file_size = self._path.stat().st_size if self._path.exists() else 0

        return {
            "categories": categories,
            "total": total,
            "schema_version": data.get("schema_version", SCHEMA_VERSION),
            "session_count": data.get("session_count", 0),
            "file_size": _human_file_size(file_size),
        }

    def export(self, output_format: str = "markdown") -> dict:
        """Export all memories as markdown or JSON."""
        data = self._load()
        if output_format == "json":
            return {"content": json.dumps(data, indent=JSON_INDENT, ensure_ascii=False)}

        return {"content": _format_as_markdown(data)}

    def about_me(self) -> dict:
        """Aggregate user profile from user, relationships, and tools categories."""
        data = self._load()
        memories = data.get("memories", {})
        lines = []

        user_entries = memories.get("user", {})
        if user_entries:
            lines.append("## User Profile")
            for key, entry in user_entries.items():
                lines.append(f"- **{key}**: {entry['value']}")

        rel_entries = memories.get("relationships", {})
        user_facing = {
            k: v for k, v in rel_entries.items()
            if "user-facing" in v.get("tags", [])
        }
        if user_facing:
            lines.append("")
            lines.append("## Relationship Context")
            for key, entry in user_facing.items():
                lines.append(f"- **{key}**: {entry['value']}")

        tools_entries = memories.get("tools", {})
        user_prefs = {
            k: v for k, v in tools_entries.items()
            if "user-preference" in v.get("tags", [])
        }
        if user_prefs:
            lines.append("")
            lines.append("## Tool Preferences")
            for key, entry in user_prefs.items():
                lines.append(f"- **{key}**: {entry['value']}")

        profile = "\n".join(lines) if lines else "No user profile data found."
        return {"profile": profile}

    def about_us(self) -> dict:
        """Aggregate relationship and relevant assistant entries."""
        data = self._load()
        memories = data.get("memories", {})
        lines = []

        rel_entries = memories.get("relationships", {})
        if rel_entries:
            lines.append("## Our Relationship")
            for key, entry in rel_entries.items():
                lines.append(f"- **{key}**: {entry['value']}")

        assistant_entries = memories.get("assistant", {})
        if assistant_entries:
            lines.append("")
            lines.append("## Assistant Identity")
            for key, entry in assistant_entries.items():
                lines.append(f"- **{key}**: {entry['value']}")

        profile = "\n".join(lines) if lines else "No relationship data found."
        return {"profile": profile}

    def reflect(self) -> dict:
        """Run lifecycle analysis on the memory store. Read-only -- no writes."""
        data = self._load()
        session_count = data.get("session_count", 0)
        return lifecycle_analyze(data, session_count)

    # -- Link operations ------------------------------------------------------

    def add_link(
        self,
        source_category: str,
        source_key: str,
        target_category: str,
        target_key: str,
        relation: str,
    ) -> dict:
        """Create a unidirectional link from source entry to target entry."""
        self._validate_category(source_category)
        self._validate_category(target_category)
        if relation not in VALID_RELATIONS:
            msg = f"Invalid relation '{relation}'. Must be one of: {', '.join(VALID_RELATIONS)}"
            raise ValueError(msg)

        target_ref = f"{target_category}.{target_key}"
        source_ref = f"{source_category}.{source_key}"

        def _mutate(data: dict) -> dict:
            memories = data.get("memories", {})

            # Validate source exists
            src_entries = memories.get(source_category, {})
            if source_key not in src_entries:
                msg = f"Source entry '{source_ref}' not found"
                raise KeyError(msg)

            # Validate target exists
            tgt_entries = memories.get(target_category, {})
            if target_key not in tgt_entries:
                msg = f"Target entry '{target_ref}' not found"
                raise KeyError(msg)

            source_entry = src_entries[source_key]
            links = source_entry.setdefault("links", [])

            # Prevent duplicate links (same target + relation)
            for existing_link in links:
                if existing_link["target"] == target_ref and existing_link["relation"] == relation:
                    return {
                        "link_created": False,
                        "reason": "duplicate",
                        "source": source_ref,
                        "target": target_ref,
                        "relation": relation,
                    }

            links.append({"target": target_ref, "relation": relation})
            return {
                "link_created": True,
                "source": source_ref,
                "target": target_ref,
                "relation": relation,
            }

        return self._read_modify_write(_mutate)

    def remove_link(
        self,
        source_category: str,
        source_key: str,
        target_category: str,
        target_key: str,
    ) -> dict:
        """Remove a link from source entry to target entry."""
        self._validate_category(source_category)
        self._validate_category(target_category)

        target_ref = f"{target_category}.{target_key}"
        source_ref = f"{source_category}.{source_key}"

        def _mutate(data: dict) -> dict:
            memories = data.get("memories", {})
            src_entries = memories.get(source_category, {})

            if source_key not in src_entries:
                msg = f"Source entry '{source_ref}' not found"
                raise KeyError(msg)

            source_entry = src_entries[source_key]
            links = source_entry.get("links", [])
            original_count = len(links)
            source_entry["links"] = [
                lk for lk in links if lk["target"] != target_ref
            ]

            if len(source_entry["links"]) == original_count:
                msg = f"No link from '{source_ref}' to '{target_ref}'"
                raise KeyError(msg)

            return {"link_removed": True, "source": source_ref, "target": target_ref}

        return self._read_modify_write(_mutate)

    def connections(self, category: str, key: str) -> dict:
        """Find all outgoing and incoming links for an entry."""
        self._validate_category(category)
        target_ref = f"{category}.{key}"

        data = self._load()
        memories = data.get("memories", {})

        # Validate entry exists
        cat_entries = memories.get(category, {})
        if key not in cat_entries:
            msg = f"Entry '{target_ref}' not found"
            raise KeyError(msg)

        entry = cat_entries[key]

        # Outgoing links
        outgoing = []
        for link in entry.get("links", []):
            target = link["target"]
            relation = link["relation"]
            tgt_cat, tgt_key = target.split(".", 1)
            tgt_entry = memories.get(tgt_cat, {}).get(tgt_key, {})
            outgoing.append({
                "target": target,
                "relation": relation,
                "entry_summary": tgt_entry.get("value", ""),
            })

        # Incoming links (reverse lookup)
        incoming = _find_incoming_links(memories, target_ref)

        return {"outgoing": outgoing, "incoming": incoming}


# -- Module-level helpers (kept out of class for readability) -----------------


def _find_match_reasons(key: str, entry: dict, query_lower: str) -> list[str]:
    """Return list of match reasons for a search query against an entry."""
    reasons = []
    if query_lower in key.lower():
        reasons.append("key")
    if query_lower in entry.get("value", "").lower():
        reasons.append("value")
    tags = entry.get("tags", [])
    if any(query_lower in tag.lower() for tag in tags):
        reasons.append("tag")
    return reasons


def _format_as_markdown(data: dict) -> str:
    """Format full memory data as markdown."""
    lines = [f"# Memory Export (schema {data.get('schema_version', '?')})"]
    lines.append(f"Session count: {data.get('session_count', 0)}")
    lines.append("")

    memories = data.get("memories", {})
    for cat_name, entries in memories.items():
        if not entries:
            continue
        lines.append(f"## {cat_name}")
        for key, entry in entries.items():
            tags_str = ", ".join(entry.get("tags", []))
            tag_suffix = f" [{tags_str}]" if tags_str else ""
            lines.append(f"- **{key}**: {entry.get('value', '')}{tag_suffix}")
        lines.append("")

    return "\n".join(lines)


def _find_auto_links(
    category: str,
    new_key: str,
    new_tags: list[str],
    cat_entries: dict[str, dict],
) -> list[dict]:
    """Find entries in the same category with 2+ tag overlap for auto-linking.

    Returns a list of link dicts (max MAX_AUTO_LINKS_PER_REMEMBER).
    """
    if not new_tags:
        return []

    new_tag_set = {t.lower() for t in new_tags}
    auto_links: list[dict] = []

    for existing_key, entry in cat_entries.items():
        if existing_key == new_key:
            continue

        existing_tags = {t.lower() for t in entry.get("tags", [])}
        overlap = len(new_tag_set & existing_tags)
        if overlap >= AUTO_LINK_TAG_OVERLAP_THRESHOLD:
            target_ref = f"{category}.{existing_key}"
            auto_links.append({
                "target": target_ref,
                "relation": AUTO_LINK_RELATION,
            })
            if len(auto_links) >= MAX_AUTO_LINKS_PER_REMEMBER:
                break

    return auto_links


def _remove_incoming_links(memories: dict, target_ref: str) -> None:
    """Remove all links pointing to target_ref from all entries in the store."""
    for _cat_name, entries in memories.items():
        for _key, entry in entries.items():
            links = entry.get("links", [])
            if links:
                entry["links"] = [
                    lk for lk in links if lk["target"] != target_ref
                ]


def _find_incoming_links(memories: dict, target_ref: str) -> list[dict]:
    """Scan all entries for links pointing to target_ref (reverse lookup)."""
    incoming: list[dict] = []
    for cat_name, entries in memories.items():
        for entry_key, entry in entries.items():
            for link in entry.get("links", []):
                if link["target"] == target_ref:
                    source_ref = f"{cat_name}.{entry_key}"
                    incoming.append({
                        "source": source_ref,
                        "relation": link["relation"],
                        "entry_summary": entry.get("value", ""),
                    })
    return incoming


def _is_fd_closed(fd: int) -> bool:
    """Check if a file descriptor is already closed."""
    try:
        os.fstat(fd)
    except OSError:
        return True
    return False
