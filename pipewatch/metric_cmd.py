"""CLI subcommands for metric recording and reporting."""

from __future__ import annotations

import argparse
import datetime
import json
from typing import List

from pipewatch.metric import (
    MetricPoint,
    aggregate,
    filter_metrics,
    load_metrics,
    save_metric,
)

_DEFAULT_PATH = ".pipewatch/metrics.jsonl"


def cmd_metric_record(args: argparse.Namespace) -> int:
    tags = {}
    for t in args.tag or []:
        if "=" in t:
            k, v = t.split("=", 1)
            tags[k.strip()] = v.strip()
    mp = MetricPoint(
        command=args.command,
        name=args.name,
        value=float(args.value),
        timestamp=datetime.datetime.utcnow().isoformat(),
        tags=tags,
    )
    path = getattr(args, "metrics_path", _DEFAULT_PATH)
    save_metric(path, mp)
    print(f"Recorded {args.name}={args.value} for '{args.command}'")
    return 0


def cmd_metric_show(args: argparse.Namespace) -> int:
    path = getattr(args, "metrics_path", _DEFAULT_PATH)
    points = load_metrics(path)
    points = filter_metrics(
        points,
        command=getattr(args, "command", None),
        name=getattr(args, "name", None),
    )
    if not points:
        print("No metrics found.")
        return 0
    agg = aggregate(points)
    print(json.dumps(agg, indent=2))
    return 0


def add_metric_subparser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("metric", help="Record and inspect numeric metrics")
    msub = p.add_subparsers(dest="metric_cmd")

    rec = msub.add_parser("record", help="Record a metric value")
    rec.add_argument("command", help="Pipeline command name")
    rec.add_argument("name", help="Metric name")
    rec.add_argument("value", type=float, help="Numeric value")
    rec.add_argument("--tag", action="append", metavar="KEY=VAL")
    rec.set_defaults(func=cmd_metric_record)

    show = msub.add_parser("show", help="Show aggregated metrics")
    show.add_argument("--command", default=None)
    show.add_argument("--name", default=None)
    show.set_defaults(func=cmd_metric_show)


def dispatch(args: argparse.Namespace) -> int:
    func = getattr(args, "func", None)
    if func is None:
        print("Usage: pipewatch metric {record,show}")
        return 1
    return func(args)
