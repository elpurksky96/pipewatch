"""CLI sub-commands for tag-based history queries."""
from __future__ import annotations
import argparse
from pipewatch.tags import parse_tags, TagFilter, describe_filter
from pipewatch.tagged_history import load_tagged_history, summarize_by_tag
from pipewatch.config import load_config


def cmd_tag_summary(args: argparse.Namespace) -> int:
    cfg = load_config(args.config) if hasattr(args, "config") and args.config else None
    history_path = (cfg.history_path if cfg and hasattr(cfg, "history_path") else None) or "pipewatch_history.json"

    include = parse_tags(args.include) if args.include else []
    exclude = parse_tags(args.exclude) if args.exclude else []
    f = TagFilter(include=include, exclude=exclude)

    entries = load_tagged_history(history_path, f)
    counts = summarize_by_tag(entries)

    print(describe_filter(f))
    print(f"Matching entries: {len(entries)}")
    if counts:
        print("Tag counts:")
        for tag, n in sorted(counts.items()):
            print(f"  {tag}: {n}")
    else:
        print("No tag data found.")
    return 0


def add_tag_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("tag-summary", help="Summarize history entries by tag")
    p.add_argument("--include", default="", help="Comma-separated tags to include")
    p.add_argument("--exclude", default="", help="Comma-separated tags to exclude")
    p.add_argument("--config", default="", help="Path to config file")
    p.set_defaults(func=cmd_tag_summary)
