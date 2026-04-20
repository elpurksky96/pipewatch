"""Tests for pipewatch.metric."""

import os
import pytest

from pipewatch.metric import (
    MetricPoint,
    aggregate,
    filter_metrics,
    from_dict,
    load_metrics,
    save_metric,
    to_dict,
)


def _mp(name="latency", value=1.5, command="etl", tags=None):
    return MetricPoint(
        command=command,
        name=name,
        value=value,
        timestamp="2024-01-01T00:00:00",
        tags=tags or {},
    )


def test_roundtrip_dict():
    mp = _mp(tags={"env": "prod"})
    assert from_dict(to_dict(mp)).value == mp.value
    assert from_dict(to_dict(mp)).tags == {"env": "prod"}


def test_load_metrics_missing_file(tmp_path):
    pts = load_metrics(str(tmp_path / "nope.jsonl"))
    assert pts == []


def test_save_and_load(tmp_path):
    path = str(tmp_path / "metrics.jsonl")
    save_metric(path, _mp(value=2.0))
    save_metric(path, _mp(value=3.0))
    pts = load_metrics(path)
    assert len(pts) == 2
    assert pts[0].value == 2.0
    assert pts[1].value == 3.0


def test_filter_by_command(tmp_path):
    path = str(tmp_path / "m.jsonl")
    save_metric(path, _mp(command="etl"))
    save_metric(path, _mp(command="other"))
    pts = filter_metrics(load_metrics(path), command="etl")
    assert all(p.command == "etl" for p in pts)
    assert len(pts) == 1


def test_filter_by_name():
    pts = [_mp(name="latency"), _mp(name="rows")]
    assert len(filter_metrics(pts, name="rows")) == 1


def test_aggregate_basic():
    pts = [_mp(value=1.0), _mp(value=3.0), _mp(value=2.0)]
    agg = aggregate(pts)
    assert agg["min"] == 1.0
    assert agg["max"] == 3.0
    assert agg["mean"] == 2.0
    assert agg["count"] == 3.0
    assert agg["last"] == 2.0


def test_aggregate_empty():
    assert aggregate([]) == {}


def test_from_dict_defaults():
    d = {"command": "c", "name": "n", "value": "5", "timestamp": "t"}
    mp = from_dict(d)
    assert mp.tags == {}
    assert mp.value == 5.0
