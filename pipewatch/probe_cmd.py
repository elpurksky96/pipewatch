"""CLI sub-commands for liveness probes."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from pipewatch.probe import check_probe, list_probes, record_probe

_DEFAULT_PATH = ".pipewatch/probes.json"


def cmd_probe_record(args: argparse.Namespace) -> int:
    """Mark a command as alive (or failed)."""
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    entry = record_probe(
        path=args.probe_file,
        command=args.command,
        success=not args.failed,
        tags=tags,
    )
    status = "ok" if entry.success else "failed"
    print(f"[probe] recorded {entry.command!r} as {status} at {entry.last_seen}")
    return 0


def cmd_probe_check(args: argparse.Namespace) -> int:
    """Exit 0 if command was seen recently, 1 otherwise."""
    alive = check_probe(
        path=args.probe_file,
        command=args.command,
        max_age_seconds=args.max_age,
    )
    if alive:
        print(f"[probe] {args.command!r} is alive (within {args.max_age}s)")
        return 0
    print(f"[probe] {args.command!r} is STALE or missing", file=sys.stderr)
    return 1


def cmd_probe_list(args: argparse.Namespace) -> int:
    """Print all recorded probes."""
    entries = list_probes(args.probe_file)
    if not entries:
        print("[probe] no probes recorded")
        return 0
    now = datetime.now(timezone.utc)
    for e in entries:
        last = datetime.fromisoformat(e.last_seen)
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        age = int((now - last).total_seconds())
        status = "ok" if e.success else "failed"
        tags_str = ",".join(e.tags) if e.tags else "-"
        print(f"  {e.command:<40} {status:<8} age={age}s  tags={tags_str}")
    return 0


def add_probe_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("probe", help="liveness probe commands")
    p.add_argument("--probe-file", default=_DEFAULT_PATH)
    sub = p.add_subparsers(dest="probe_cmd")

    rec = sub.add_parser("record", help="record a liveness heartbeat")
    rec.add_argument("command")
    rec.add_argument("--failed", action="store_true", help="mark as failed run")
    rec.add_argument("--tags", default="", help="comma-separated tags")

    chk = sub.add_parser("check", help="check if command is alive")
    chk.add_argument("command")
    chk.add_argument("--max-age", type=float, default=3600.0, help="seconds")

    sub.add_parser("list", help="list all probes")


def dispatch(args: argparse.Namespace) -> int:
    return {
        "record": cmd_probe_record,
        "check": cmd_probe_check,
        "list": cmd_probe_list,
    }.get(args.probe_cmd, lambda _: (print("Usage: pipewatch probe <record|check|list>", file=sys.stderr), 1)[-1])(args)
