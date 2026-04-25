"""Pipeline graph visualization and status rollup."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PipelineNode:
    name: str
    command: str
    depends_on: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    last_status: Optional[str] = None  # "success", "failure", "timeout", None
    last_duration: Optional[float] = None


def to_dict(node: PipelineNode) -> dict:
    return {
        "name": node.name,
        "command": node.command,
        "depends_on": node.depends_on,
        "tags": node.tags,
        "last_status": node.last_status,
        "last_duration": node.last_duration,
    }


def from_dict(d: dict) -> PipelineNode:
    return PipelineNode(
        name=d["name"],
        command=d["command"],
        depends_on=d.get("depends_on", []),
        tags=d.get("tags", []),
        last_status=d.get("last_status"),
        last_duration=d.get("last_duration"),
    )


def build_pipeline(nodes: List[PipelineNode]) -> Dict[str, PipelineNode]:
    """Return a name-keyed dict of nodes."""
    return {n.name: n for n in nodes}


def ready_nodes(graph: Dict[str, PipelineNode]) -> List[str]:
    """Return names of nodes whose dependencies have all succeeded."""
    ready = []
    for name, node in graph.items():
        if node.last_status == "success":
            continue
        deps_ok = all(
            graph[dep].last_status == "success"
            for dep in node.depends_on
            if dep in graph
        )
        if deps_ok:
            ready.append(name)
    return ready


def pipeline_status(graph: Dict[str, PipelineNode]) -> str:
    """Return overall pipeline status."""
    statuses = [n.last_status for n in graph.values()]
    if any(s == "failure" for s in statuses):
        return "failure"
    if any(s == "timeout" for s in statuses):
        return "timeout"
    if all(s == "success" for s in statuses):
        return "success"
    return "pending"


def format_pipeline(graph: Dict[str, PipelineNode]) -> str:
    """Return a human-readable pipeline summary."""
    lines = ["Pipeline status: " + pipeline_status(graph), ""]
    for name, node in graph.items():
        status = node.last_status or "pending"
        dur = f"  ({node.last_duration:.1f}s)" if node.last_duration is not None else ""
        deps = " <- [" + ", ".join(node.depends_on) + "]" if node.depends_on else ""
        lines.append(f"  {name}{deps}  [{status}]{dur}")
    return "\n".join(lines)
