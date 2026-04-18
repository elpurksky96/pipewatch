"""Tag-based filtering and labeling for pipeline runs."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TagFilter:
    include: List[str] = field(default_factory=list)
    exclude: List[str] = field(default_factory=list)


def parse_tags(raw: str) -> List[str]:
    """Parse comma-separated tag string into a list of stripped tags."""
    if not raw or not raw.strip():
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


def matches_filter(tags: List[str], f: TagFilter) -> bool:
    """Return True if tags satisfy the filter (include/exclude rules)."""
    tag_set = set(tags)
    if f.include and not tag_set.intersection(f.include):
        return False
    if f.exclude and tag_set.intersection(f.exclude):
        return False
    return True


def filter_by_tags(entries: list, f: TagFilter) -> list:
    """Filter a list of objects that have a .tags attribute."""
    return [e for e in entries if matches_filter(getattr(e, "tags", []), f)]


def describe_filter(f: TagFilter) -> str:
    parts = []
    if f.include:
        parts.append("include=" + ",".join(sorted(f.include)))
    if f.exclude:
        parts.append("exclude=" + ",".join(sorted(f.exclude)))
    return "TagFilter(" + "; ".join(parts) + ")" if parts else "TagFilter(all)"
