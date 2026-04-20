"""CLI subcommands for managing pipeline checkpoints."""

from __future__ import annotations

import argparse
import json
import sys

from pipewatch.checkpoint import (
    clear_checkpoints,
    get_checkpoint,
    load_checkpoints,
    save_checkpoint,
)

DEFAULT_PATH = ".pipewatch_checkpoints.json"


def cmd_checkpoint_set(args: argparse.Namespace) -> int:
    path = getattr(args, "checkpoint_path", DEFAULT_PATH)
    meta = {}
    for item in getattr(args, "meta", []) or []:
        if "=" in item:
            k, v = item.split("=", 1)
            meta[k.strip()] = v.strip()
    cp = save_checkpoint(path, args.name, args.command, meta)
    print(f"Checkpoint '{cp.name}' saved for command '{cp.command}' at {cp.reached_at}")
    return 0


def cmd_checkpoint_get(args: argparse.Namespace) -> int:
    path = getattr(args, "checkpoint_path", DEFAULT_PATH)
    cp = get_checkpoint(path, args.name, args.command)
    if cp is None:
        print(f"No checkpoint '{args.name}' found for command '{args.command}'.")
        return 1
    print(json.dumps({
        "name": cp.name,
        "command": cp.command,
        "reached_at": cp.reached_at,
        "metadata": cp.metadata,
    }, indent=2))
    return 0


def cmd_checkpoint_list(args: argparse.Namespace) -> int:
    path = getattr(args, "checkpoint_path", DEFAULT_PATH)
    checkpoints = load_checkpoints(path)
    if not checkpoints:
        print("No checkpoints recorded.")
        return 0
    for cp in checkpoints:
        meta_str = f" {cp.metadata}" if cp.metadata else ""
        print(f"  [{cp.reached_at}] {cp.command} -> {cp.name}{meta_str}")
    return 0


def cmd_checkpoint_clear(args: argparse.Namespace) -> int:
    path = getattr(args, "checkpoint_path", DEFAULT_PATH)
    command = getattr(args, "command", None)
    removed = clear_checkpoints(path, command)
    scope = f"for '{command}'" if command else "all"
    print(f"Cleared {removed} checkpoint(s) ({scope}).")
    return 0


def add_checkpoint_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("checkpoint", help="Manage pipeline checkpoints")
    p.add_argument("--checkpoint-path", default=DEFAULT_PATH)
    sub = p.add_subparsers(dest="checkpoint_action")

    ps = sub.add_parser("set", help="Record a checkpoint")
    ps.add_argument("name")
    ps.add_argument("command")
    ps.add_argument("--meta", nargs="*", metavar="KEY=VALUE")

    pg = sub.add_parser("get", help="Retrieve a checkpoint")
    pg.add_argument("name")
    pg.add_argument("command")

    sub.add_parser("list", help="List all checkpoints")

    pc = sub.add_parser("clear", help="Clear checkpoints")
    pc.add_argument("--command", default=None)


def dispatch(args: argparse.Namespace) -> int:
    action = getattr(args, "checkpoint_action", None)
    if action == "set":
        return cmd_checkpoint_set(args)
    if action == "get":
        return cmd_checkpoint_get(args)
    if action == "list":
        return cmd_checkpoint_list(args)
    if action == "clear":
        return cmd_checkpoint_clear(args)
    print("Usage: pipewatch checkpoint {set,get,list,clear}", file=sys.stderr)
    return 1
