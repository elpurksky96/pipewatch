"""Dependency tracking: define named pipeline steps and their prerequisites."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DependencyNode:
    name: str
    command: str
    depends_on: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


def to_dict(node: DependencyNode) -> dict:
    return {
        "name": node.name,
        "command": node.command,
        "depends_on": list(node.depends_on),
        "tags": list(node.tags),
    }


def from_dict(d: dict) -> DependencyNode:
    return DependencyNode(
        name=d["name"],
        command=d["command"],
        depends_on=d.get("depends_on", []),
        tags=d.get("tags", []),
    )


def build_graph(nodes: List[DependencyNode]) -> Dict[str, List[str]]:
    """Return adjacency map: name -> list of names it depends on."""
    return {n.name: list(n.depends_on) for n in nodes}


def topological_order(nodes: List[DependencyNode]) -> List[str]:
    """Return names in a valid execution order (raises on cycles)."""
    graph = build_graph(nodes)
    visited: set = set()
    order: List[str] = []
    in_stack: set = set()

    def visit(name: str) -> None:
        if name in in_stack:
            raise ValueError(f"Cycle detected at node '{name}'")
        if name in visited:
            return
        in_stack.add(name)
        for dep in graph.get(name, []):
            visit(dep)
        in_stack.discard(name)
        visited.add(name)
        order.append(name)

    for n in graph:
        visit(n)
    return order


def find_missing_deps(nodes: List[DependencyNode]) -> Dict[str, List[str]]:
    """Return map of node name -> list of declared deps not defined in the graph."""
    names = {n.name for n in nodes}
    missing: Dict[str, List[str]] = {}
    for node in nodes:
        absent = [d for d in node.depends_on if d not in names]
        if absent:
            missing[node.name] = absent
    return missing


def describe_node(node: DependencyNode) -> str:
    parts = [f"[{node.name}] {node.command}"]
    if node.depends_on:
        parts.append(f"  depends on: {', '.join(node.depends_on)}")
    if node.tags:
        parts.append(f"  tags: {', '.join(node.tags)}")
    return "\n".join(parts)
