"""Tests for pipewatch.dependency."""
import pytest

from pipewatch.dependency import (
    DependencyNode,
    build_graph,
    describe_node,
    find_missing_deps,
    from_dict,
    to_dict,
    topological_order,
)


def _node(name: str, depends_on=None, tags=None) -> DependencyNode:
    return DependencyNode(
        name=name,
        command=f"run_{name}.sh",
        depends_on=depends_on or [],
        tags=tags or [],
    )


def test_roundtrip_dict():
    node = _node("ingest", depends_on=["fetch"], tags=["etl"])
    assert from_dict(to_dict(node)) == node


def test_build_graph_keys():
    nodes = [_node("a"), _node("b", depends_on=["a"])]
    graph = build_graph(nodes)
    assert graph == {"a": [], "b": ["a"]}


def test_topological_order_simple():
    nodes = [_node("b", depends_on=["a"]), _node("a")]
    order = topological_order(nodes)
    assert order.index("a") < order.index("b")


def test_topological_order_chain():
    nodes = [
        _node("c", depends_on=["b"]),
        _node("b", depends_on=["a"]),
        _node("a"),
    ]
    order = topological_order(nodes)
    assert order.index("a") < order.index("b") < order.index("c")


def test_topological_order_cycle_raises():
    nodes = [
        _node("a", depends_on=["b"]),
        _node("b", depends_on=["a"]),
    ]
    with pytest.raises(ValueError, match="Cycle"):
        topological_order(nodes)


def test_find_missing_deps_none():
    nodes = [_node("a"), _node("b", depends_on=["a"])]
    assert find_missing_deps(nodes) == {}


def test_find_missing_deps_detects_absent():
    nodes = [_node("b", depends_on=["a", "ghost"])]
    missing = find_missing_deps(nodes)
    assert "b" in missing
    assert "ghost" in missing["b"]
    assert "a" in missing["b"]


def test_describe_node_includes_name_and_command():
    node = _node("ingest", depends_on=["fetch"], tags=["etl"])
    desc = describe_node(node)
    assert "ingest" in desc
    assert "run_ingest.sh" in desc
    assert "fetch" in desc
    assert "etl" in desc


def test_describe_node_no_deps_no_tags():
    node = _node("standalone")
    desc = describe_node(node)
    assert "depends on" not in desc
    assert "tags" not in desc
