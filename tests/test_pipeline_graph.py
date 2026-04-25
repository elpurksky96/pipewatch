"""Tests for pipewatch.pipeline_graph."""
import pytest
from pipewatch.pipeline_graph import (
    PipelineNode,
    to_dict,
    from_dict,
    build_pipeline,
    ready_nodes,
    pipeline_status,
    format_pipeline,
)


def _node(name, depends_on=None, status=None, duration=None):
    return PipelineNode(
        name=name,
        command=f"run_{name}.sh",
        depends_on=depends_on or [],
        last_status=status,
        last_duration=duration,
    )


def test_roundtrip_dict():
    n = _node("ingest", depends_on=["extract"], status="success", duration=3.5)
    assert from_dict(to_dict(n)).name == "ingest"
    assert from_dict(to_dict(n)).last_status == "success"
    assert from_dict(to_dict(n)).depends_on == ["extract"]


def test_from_dict_defaults():
    n = from_dict({"name": "x", "command": "echo x"})
    assert n.depends_on == []
    assert n.last_status is None
    assert n.last_duration is None


def test_build_pipeline_keys():
    nodes = [_node("a"), _node("b")]
    graph = build_pipeline(nodes)
    assert set(graph.keys()) == {"a", "b"}


def test_ready_nodes_no_deps():
    nodes = [_node("a"), _node("b")]
    graph = build_pipeline(nodes)
    ready = ready_nodes(graph)
    assert "a" in ready and "b" in ready


def test_ready_nodes_dep_not_done():
    nodes = [_node("a"), _node("b", depends_on=["a"])]
    graph = build_pipeline(nodes)
    ready = ready_nodes(graph)
    assert "a" in ready
    assert "b" not in ready


def test_ready_nodes_dep_succeeded():
    nodes = [_node("a", status="success"), _node("b", depends_on=["a"])]
    graph = build_pipeline(nodes)
    ready = ready_nodes(graph)
    assert "b" in ready
    assert "a" not in ready  # already done


def test_pipeline_status_all_success():
    nodes = [_node("a", status="success"), _node("b", status="success")]
    graph = build_pipeline(nodes)
    assert pipeline_status(graph) == "success"


def test_pipeline_status_failure():
    nodes = [_node("a", status="success"), _node("b", status="failure")]
    graph = build_pipeline(nodes)
    assert pipeline_status(graph) == "failure"


def test_pipeline_status_timeout():
    nodes = [_node("a", status="success"), _node("b", status="timeout")]
    graph = build_pipeline(nodes)
    assert pipeline_status(graph) == "timeout"


def test_pipeline_status_pending():
    nodes = [_node("a", status="success"), _node("b")]
    graph = build_pipeline(nodes)
    assert pipeline_status(graph) == "pending"


def test_format_pipeline_contains_names():
    nodes = [_node("ingest", status="success", duration=2.0), _node("transform", depends_on=["ingest"])]
    graph = build_pipeline(nodes)
    out = format_pipeline(graph)
    assert "ingest" in out
    assert "transform" in out
    assert "success" in out
    assert "2.0s" in out
