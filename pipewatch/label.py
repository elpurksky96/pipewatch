"""Label-based grouping and filtering for pipeline runs."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LabelSet:
    labels: Dict[str, str] = field(default_factory=dict)

    def get(self, key: str) -> Optional[str]:
        return self.labels.get(key)

    def matches(self, selector: Dict[str, str]) -> bool:
        return all(self.labels.get(k) == v for k, v in selector.items())

    def as_dict(self) -> Dict[str, str]:
        return dict(self.labels)


def parse_labels(raw: List[str]) -> LabelSet:
    """Parse ["key=value", ...] into a LabelSet."""
    labels: Dict[str, str] = {}
    for item in raw:
        if "=" in item:
            k, _, v = item.partition("=")
            labels[k.strip()] = v.strip()
    return LabelSet(labels=labels)


def parse_selector(raw: str) -> Dict[str, str]:
    """Parse 'key=value,key2=value2' into a dict."""
    selector: Dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if "=" in part:
            k, _, v = part.partition("=")
            selector[k.strip()] = v.strip()
    return selector


def filter_by_labels(entries, selector: Dict[str, str]):
    """Filter entries that have a .labels LabelSet matching selector."""
    if not selector:
        return list(entries)
    return [e for e in entries if e.labels.matches(selector)]


def group_by_label(entries, key: str) -> Dict[str, list]:
    """Group entries by the value of a specific label key."""
    groups: Dict[str, list] = {}
    for e in entries:
        val = e.labels.get(key) or "(none)"
        groups.setdefault(val, []).append(e)
    return groups
