"""History entries with attached LabelSets."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from pipewatch.label import LabelSet, parse_labels
from pipewatch.history import HistoryEntry, load_history, append_entry


@dataclass
class LabeledEntry:
    entry: HistoryEntry
    labels: LabelSet

    @property
    def command(self) -> str:
        return self.entry.command

    @property
    def success(self) -> bool:
        return self.entry.success

    @property
    def duration(self) -> float:
        return self.entry.duration


def make_labeled_entry(entry: HistoryEntry, raw_labels: List[str]) -> LabeledEntry:
    return LabeledEntry(entry=entry, labels=parse_labels(raw_labels))


def load_labeled_history(path: str, raw_labels: List[str]) -> List[LabeledEntry]:
    entries = load_history(path)
    label_set = parse_labels(raw_labels)
    return [LabeledEntry(entry=e, labels=label_set) for e in entries]


def summarize_by_label(entries: List[LabeledEntry], key: str) -> Dict[str, Dict]:
    from pipewatch.label import group_by_label
    groups = group_by_label(entries, key)
    result = {}
    for val, grp in groups.items():
        total = len(grp)
        passed = sum(1 for e in grp if e.success)
        avg_dur = sum(e.duration for e in grp) / total if total else 0.0
        result[val] = {"total": total, "passed": passed, "avg_duration": round(avg_dur, 3)}
    return result
