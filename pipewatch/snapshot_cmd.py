"""CLI helpers for snapshot capture and comparison."""
from __future__ import annotations

import sys
from typing import Optional

from pipewatch.history import load_history
from pipewatch.snapshot import latest_snapshot, save_snapshot, diff_snapshots
from pipewatch.snapshot_builder import build_snapshot, format_diff


def cmd_snapshot(history_path: str, snapshot_path: str, label: str) -> int:
    """Capture a new snapshot from current history and print diff."""
    entries = load_history(history_path)
    if not entries:
        print("No history entries found — nothing to snapshot.", file=sys.stderr)
        return 1

    new_snap = build_snapshot(label, entries)
    old_snap = latest_snapshot(snapshot_path)

    save_snapshot(snapshot_path, new_snap)
    print(f"Snapshot '{label}' saved ({new_snap.total_runs} runs, "
          f"{new_snap.success_rate*100:.1f}% success).")

    if old_snap:
        diff = diff_snapshots(old_snap, new_snap)
        print(format_diff(diff))
    else:
        print("First snapshot recorded — no previous baseline to compare.")

    return 0


def cmd_show_snapshots(snapshot_path: str) -> int:
    """Print all stored snapshots in a simple table."""
    from pipewatch.snapshot import load_snapshots
    snaps = load_snapshots(snapshot_path)
    if not snaps:
        print("No snapshots found.")
        return 0
    header = f"{'Label':<20} {'Timestamp':<30} {'Runs':>6} {'Success%':>9} {'AvgDur':>8} {'Timeouts':>9}"
    print(header)
    print("-" * len(header))
    for s in snaps:
        print(f"{s.label:<20} {s.timestamp:<30} {s.total_runs:>6} "
              f"{s.success_rate*100:>8.1f}% {s.avg_duration:>8.2f} {s.timeout_count:>9}")
    return 0
