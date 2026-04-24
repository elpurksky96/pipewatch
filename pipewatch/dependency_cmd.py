"""CLI sub-commands for dependency graph inspection."""
from __future__ import annotations

import json
from argparse import ArgumentParser, Namespace
from typing import List

from pipewatch.dependency import (
    DependencyNode,
    describe_node,
    find_missing_deps,
    from_dict,
    topological_order,
)


def _load_nodes(path: str) -> List[DependencyNode]:
    with open(path) as fh:
        raw = json.load(fh)
    if not isinstance(raw, list):
        raise ValueError("Dependency file must contain a JSON array")
    return [from_dict(item) for item in raw]


def cmd_dep_list(args: Namespace) -> int:
    nodes = _load_nodes(args.file)
    for node in nodes:
        print(describe_node(node))
        print()
    return 0


def cmd_dep_order(args: Namespace) -> int:
    nodes = _load_nodes(args.file)
    missing = find_missing_deps(nodes)
    if missing:
        for name, deps in missing.items():
            print(f"ERROR: '{name}' has undefined dependencies: {', '.join(deps)}")
        return 1
    try:
        order = topological_order(nodes)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    print("Execution order:")
    for i, name in enumerate(order, 1):
        print(f"  {i}. {name}")
    return 0


def cmd_dep_check(args: Namespace) -> int:
    nodes = _load_nodes(args.file)
    missing = find_missing_deps(nodes)
    if missing:
        print("Missing dependencies detected:")
        for name, deps in missing.items():
            print(f"  {name}: {', '.join(deps)}")
        return 1
    try:
        topological_order(nodes)
    except ValueError as exc:
        print(f"Cycle error: {exc}")
        return 1
    print("Dependency graph is valid.")
    return 0


def add_dependency_subparser(sub: ArgumentParser) -> None:
    p = sub.add_parser("dep", help="Dependency graph commands")
    p.add_argument("--file", default="pipeline.json", help="Path to dependency JSON file")
    sp = p.add_subparsers(dest="dep_cmd")

    sp.add_parser("list", help="List all nodes")
    sp.add_parser("order", help="Show topological execution order")
    sp.add_parser("check", help="Validate dependency graph")


def dispatch(args: Namespace) -> int:
    cmd = getattr(args, "dep_cmd", None)
    if cmd == "list":
        return cmd_dep_list(args)
    if cmd == "order":
        return cmd_dep_order(args)
    if cmd == "check":
        return cmd_dep_check(args)
    print("Usage: pipewatch dep {list|order|check}")
    return 1
