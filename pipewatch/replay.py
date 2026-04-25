"""Replay historical runs for debugging or dry-run validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.history import HistoryEntry, load_history


@dataclass
class ReplayResult:
    command: str
    entries: List[HistoryEntry]
    replayed: int
    skipped: int
    errors: List[str] = field(default_factory=list)


def _matches_command(entry: HistoryEntry, command: str) -> bool:
    return entry.command == command


def load_entries_for_command(
    command: str,
    history_path: str,
    limit: Optional[int] = None,
) -> List[HistoryEntry]:
    """Return history entries for a specific command, newest first."""
    all_entries = load_history(history_path)
    matched = [e for e in reversed(all_entries) if _matches_command(e, command)]
    if limit is not None:
        matched = matched[:limit]
    return matched


def replay(
    command: str,
    history_path: str,
    limit: Optional[int] = None,
    only_failures: bool = False,
) -> ReplayResult:
    """Simulate replaying past runs for a command.

    Returns a ReplayResult summarising which entries would be replayed.
    No actual subprocess is spawned; this is for inspection/dry-run use.
    """
    entries = load_entries_for_command(command, history_path, limit=limit)
    replayed = 0
    skipped = 0
    errors: List[str] = []

    for entry in entries:
        if only_failures and entry.success:
            skipped += 1
            continue
        replayed += 1

    return ReplayResult(
        command=command,
        entries=entries,
        replayed=replayed,
        skipped=skipped,
        errors=errors,
    )


def format_replay_summary(result: ReplayResult) -> str:
    lines = [
        f"Replay summary for: {result.command}",
        f"  Total entries found : {len(result.entries)}",
        f"  Would replay        : {result.replayed}",
        f"  Skipped             : {result.skipped}",
    ]
    if result.errors:
        lines.append("  Errors:")
        for err in result.errors:
            lines.append(f"    - {err}")
    return "\n".join(lines)
