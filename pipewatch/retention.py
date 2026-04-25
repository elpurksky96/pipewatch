"""History retention policy: prune old entries based on age or count."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class RetentionPolicy:
    max_entries: Optional[int] = None   # keep at most N most-recent entries
    max_days: Optional[float] = None    # drop entries older than N days


def parse_policy(raw: dict) -> RetentionPolicy:
    """Build a RetentionPolicy from a plain dict (e.g. loaded from config)."""
    return RetentionPolicy(
        max_entries=raw.get("max_entries"),
        max_days=raw.get("max_days"),
    )


def policy_to_dict(policy: RetentionPolicy) -> dict:
    out: dict = {}
    if policy.max_entries is not None:
        out["max_entries"] = policy.max_entries
    if policy.max_days is not None:
        out["max_days"] = policy.max_days
    return out


def _timestamp(entry: object) -> Optional[str]:
    """Return the ISO timestamp from an entry dict or object."""
    if isinstance(entry, dict):
        return entry.get("timestamp") or entry.get("started_at")
    return getattr(entry, "timestamp", None) or getattr(entry, "started_at", None)


def apply_retention(entries: list, policy: RetentionPolicy) -> list:
    """Return a pruned copy of *entries* according to *policy*.

    Entries are assumed to be ordered oldest-first.  Both rules are applied
    when set; the stricter one wins.
    """
    import datetime

    result = list(entries)

    if policy.max_days is not None:
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            days=policy.max_days
        )
        kept = []
        for e in result:
            ts = _timestamp(e)
            if ts is None:
                kept.append(e)
                continue
            try:
                dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                if dt >= cutoff:
                    kept.append(e)
            except ValueError:
                kept.append(e)
        result = kept

    if policy.max_entries is not None and len(result) > policy.max_entries:
        result = result[-policy.max_entries :]

    return result


def prune_history_file(path: Path, policy: RetentionPolicy) -> int:
    """Prune the JSONL history file at *path* in-place.

    Returns the number of entries removed.
    """
    if not path.exists():
        return 0

    raw_lines = path.read_text().splitlines()
    entries = []
    for line in raw_lines:
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    pruned = apply_retention(entries, policy)
    removed = len(entries) - len(pruned)

    if removed > 0:
        path.write_text(
            "\n".join(json.dumps(e) for e in pruned) + ("\n" if pruned else "")
        )

    return removed
