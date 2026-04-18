"""Helpers to attach and query tags on history entries."""
from __future__ import annotations
from typing import List, Optional
from pipewatch.history import HistoryEntry, load_history, append_entry
from pipewatch.tags import TagFilter, filter_by_tags
import dataclasses


def make_entry_with_tags(
    command: str,
    tags: List[str],
    success: bool,
    duration: float,
    stderr: str = "",
    timed_out: bool = False,
) -> HistoryEntry:
    """Create a HistoryEntry and attach tags via extra metadata field if available,
    or store them as a plain attribute for filtering purposes."""
    entry = HistoryEntry(
        command=command,
        success=success,
        duration=duration,
        stderr=stderr,
        timed_out=timed_out,
    )
    # Attach tags as a dynamic attribute for filter_by_tags compatibility
    object.__setattr__(entry, "tags", tags) if dataclasses.is_dataclass(entry) else setattr(entry, "tags", tags)
    return entry


def load_tagged_history(path: str, f: Optional[TagFilter] = None) -> List[HistoryEntry]:
    """Load history and optionally filter by tags."""
    entries = load_history(path)
    for e in entries:
        if not hasattr(e, "tags"):
            e.tags = []
    if f is None:
        return entries
    return filter_by_tags(entries, f)


def summarize_by_tag(entries: list) -> dict:
    """Return a dict mapping each tag to count of entries carrying it."""
    counts: dict = {}
    for e in entries:
        for tag in getattr(e, "tags", []):
            counts[tag] = counts.get(tag, 0) + 1
    return counts
