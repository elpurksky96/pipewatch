"""CLI subcommands for pipeline graph management."""
from __future__ import annotations
import json
from pathlib import Path
from typing import List

from pipewatch.pipeline_graph import (
    PipelineNode,
    from_dict,
    to_dict,
    build_pipeline,
    ready_nodes,
    format_pipeline,
    pipeline_status,
)


def _load_nodes(path: str) -> List[PipelineNode]:
    p = Path(path)
    if not p.exists():
        return []
    raw = json.loads(p.read_text())
    return [from_dict(d) for d in raw]


def cmd_pipeline_show(args) -> int:
    nodes = _load_nodes(args.pipeline_file)
    if not nodes:
        print("No pipeline nodes found.")
        return 1
    graph = build_pipeline(nodes)
    print(format_pipeline(graph))
    return 0


def cmd_pipeline_ready(args) -> int:
    nodes = _load_nodes(args.pipeline_file)
    if not nodes:
        print("No pipeline nodes found.")
        return 1
    graph = build_pipeline(nodes)
    ready = ready_nodes(graph)
    if not ready:
        print("No nodes are currently ready to run.")
    else:
        print("Ready to run:")
        for name in ready:
            print(f"  {name}")
    return 0


def cmd_pipeline_status(args) -> int:
    nodes = _load_nodes(args.pipeline_file)
    if not nodes:
        print("No pipeline nodes found.")
        return 1
    graph = build_pipeline(nodes)
    status = pipeline_status(graph)
    print(status)
    return 0 if status == "success" else 1


def add_pipeline_subparser(subparsers) -> None:
    p = subparsers.add_parser("pipeline", help="Manage pipeline graphs")
    p.add_argument("--pipeline-file", default="pipeline.json", help="Path to pipeline JSON file")
    sub = p.add_subparsers(dest="pipeline_cmd")

    sub.add_parser("show", help="Show pipeline status")
    sub.add_parser("ready", help="List nodes ready to run")
    sub.add_parser("status", help="Print overall pipeline status")


def dispatch(args) -> int:
    cmd = getattr(args, "pipeline_cmd", None)
    if cmd == "show":
        return cmd_pipeline_show(args)
    if cmd == "ready":
        return cmd_pipeline_ready(args)
    if cmd == "status":
        return cmd_pipeline_status(args)
    print("No pipeline subcommand given. Use show, ready, or status.")
    return 1
