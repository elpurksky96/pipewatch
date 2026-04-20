"""Tests for pipewatch.metric_cmd."""

import argparse
import json
import pytest

from pipewatch.metric_cmd import cmd_metric_record, cmd_metric_show
from pipewatch.metric import load_metrics


def _args(**kwargs):
    base = dict(
        command="etl",
        name="latency",
        value=1.5,
        tag=None,
        func=None,
        metric_cmd=None,
    )
    base.update(kwargs)
    ns = argparse.Namespace(**base)
    return ns


def test_cmd_metric_record_creates_entry(tmp_path):
    path = str(tmp_path / "m.jsonl")
    args = _args()
    args.metrics_path = path
    rc = cmd_metric_record(args)
    assert rc == 0
    pts = load_metrics(path)
    assert len(pts) == 1
    assert pts[0].name == "latency"
    assert pts[0].value == 1.5


def test_cmd_metric_record_with_tags(tmp_path):
    path = str(tmp_path / "m.jsonl")
    args = _args(tag=["env=prod", "region=us"])
    args.metrics_path = path
    cmd_metric_record(args)
    pts = load_metrics(path)
    assert pts[0].tags == {"env": "prod", "region": "us"}


def test_cmd_metric_show_no_data(tmp_path, capsys):
    path = str(tmp_path / "m.jsonl")
    args = _args(command=None, name=None)
    args.metrics_path = path
    rc = cmd_metric_show(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No metrics" in out


def test_cmd_metric_show_aggregated(tmp_path, capsys):
    from pipewatch.metric import MetricPoint, save_metric
    import datetime

    path = str(tmp_path / "m.jsonl")
    for v in [1.0, 2.0, 3.0]:
        save_metric(
            path,
            MetricPoint(
                command="etl",
                name="rows",
                value=v,
                timestamp=datetime.datetime.utcnow().isoformat(),
            ),
        )
    args = _args(command="etl", name="rows")
    args.metrics_path = path
    rc = cmd_metric_show(args)
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["mean"] == 2.0
    assert data["count"] == 3.0


def test_cmd_metric_record_multiple(tmp_path):
    path = str(tmp_path / "m.jsonl")
    for v in [10.0, 20.0]:
        args = _args(value=v)
        args.metrics_path = path
        cmd_metric_record(args)
    pts = load_metrics(path)
    assert len(pts) == 2
