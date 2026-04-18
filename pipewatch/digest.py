"""Daily/periodic digest summarizing pipeline history across tags."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
from pipewatch.history import HistoryEntry
from pipewatch.report import _success_rate, _avg_duration, _timeout_count


@dataclass
class DigestSection:
    label: str
    total: int
    success_rate: float
    avg_duration: float
    timeouts: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "total": self.total,
            "success_rate": round(self.success_rate, 3),
            "avg_duration": round(self.avg_duration, 2),
            "timeouts": self.timeouts,
        }


@dataclass
class Digest:
    sections: List[DigestSection]

    def to_dict(self) -> Dict[str, Any]:
        return {"sections": [s.to_dict() for s in self.sections]}


def _section_from_entries(label: str, entries: List[HistoryEntry]) -> DigestSection:
    return DigestSection(
        label=label,
        total=len(entries),
        success_rate=_success_rate(entries),
        avg_duration=_avg_duration(entries),
        timeouts=_timeout_count(entries),
    )


def build_digest(entries: List[HistoryEntry], group_by_tag: bool = False) -> Digest:
    """Build a digest from history entries, optionally grouped by first tag."""
    if not group_by_tag:
        return Digest(sections=[_section_from_entries("all", entries)])

    groups: Dict[str, List[HistoryEntry]] = {}
    for e in entries:
        tags = getattr(e, "tags", []) or []
        key = tags[0] if tags else "untagged"
        groups.setdefault(key, []).append(e)

    sections = [_section_from_entries(label, group) for label, group in sorted(groups.items())]
    return Digest(sections=sections)


def format_digest(digest: Digest) -> str:
    """Render a digest as a human-readable string."""
    lines = ["=== Pipewatch Digest ==="]
    for s in digest.sections:
        status = "OK" if s.success_rate >= 1.0 else ("WARN" if s.success_rate >= 0.5 else "FAIL")
        lines.append(
            f"[{status}] {s.label}: {s.total} runs, "
            f"{s.success_rate*100:.0f}% success, "
            f"avg {s.avg_duration:.1f}s, "
            f"{s.timeouts} timeout(s)"
        )
    return "\n".join(lines)
