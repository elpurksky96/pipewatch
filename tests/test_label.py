"""Tests for pipewatch.label."""
import pytest
from pipewatch.label import (
    LabelSet, parse_labels, parse_selector, filter_by_labels, group_by_label
)
from dataclasses import dataclass, field


@dataclass
class _Obj:
    labels: LabelSet
    name: str = "x"


def test_parse_labels_normal():
    ls = parse_labels(["env=prod", "team=data"])
    assert ls.get("env") == "prod"
    assert ls.get("team") == "data"


def test_parse_labels_empty():
    ls = parse_labels([])
    assert ls.as_dict() == {}


def test_parse_labels_ignores_no_equals():
    ls = parse_labels(["badlabel", "env=staging"])
    assert ls.get("env") == "staging"
    assert ls.get("badlabel") is None


def test_label_set_matches_subset():
    ls = parse_labels(["env=prod", "team=data"])
    assert ls.matches({"env": "prod"})
    assert not ls.matches({"env": "staging"})


def test_parse_selector():
    sel = parse_selector("env=prod,team=data")
    assert sel == {"env": "prod", "team": "data"}


def test_filter_by_labels_empty_selector_returns_all():
    objs = [_Obj(labels=parse_labels(["env=prod"])), _Obj(labels=parse_labels(["env=dev"]))]
    assert filter_by_labels(objs, {}) == objs


def test_filter_by_labels_with_selector():
    a = _Obj(labels=parse_labels(["env=prod"]), name="a")
    b = _Obj(labels=parse_labels(["env=dev"]), name="b")
    result = filter_by_labels([a, b], {"env": "prod"})
    assert result == [a]


def test_group_by_label():
    a = _Obj(labels=parse_labels(["env=prod"]), name="a")
    b = _Obj(labels=parse_labels(["env=prod"]), name="b")
    c = _Obj(labels=parse_labels(["env=dev"]), name="c")
    groups = group_by_label([a, b, c], "env")
    assert set(groups.keys()) == {"prod", "dev"}
    assert len(groups["prod"]) == 2


def test_group_by_label_missing_key():
    a = _Obj(labels=parse_labels([]), name="a")
    groups = group_by_label([a], "env")
    assert "(none)" in groups
