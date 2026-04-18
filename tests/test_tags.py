"""Tests for pipewatch.tags."""
import pytest
from pipewatch.tags import (
    parse_tags,
    matches_filter,
    filter_by_tags,
    describe_filter,
    TagFilter,
)
from dataclasses import dataclass, field
from typing import List


@dataclass
class _Obj:
    name: str
    tags: List[str] = field(default_factory=list)


def test_parse_tags_normal():
    assert parse_tags("etl,nightly,prod") == ["etl", "nightly", "prod"]


def test_parse_tags_empty():
    assert parse_tags("") == []
    assert parse_tags("   ") == []


def test_parse_tags_strips_whitespace():
    assert parse_tags(" a , b , c ") == ["a", "b", "c"]


def test_matches_filter_no_rules():
    assert matches_filter(["etl"], TagFilter()) is True


def test_matches_filter_include_hit():
    assert matches_filter(["etl", "prod"], TagFilter(include=["prod"])) is True


def test_matches_filter_include_miss():
    assert matches_filter(["etl"], TagFilter(include=["prod"])) is False


def test_matches_filter_exclude_hit():
    assert matches_filter(["etl", "debug"], TagFilter(exclude=["debug"])) is False


def test_matches_filter_exclude_miss():
    assert matches_filter(["etl"], TagFilter(exclude=["debug"])) is True


def test_filter_by_tags():
    objs = [
        _Obj("a", ["etl", "prod"]),
        _Obj("b", ["etl", "dev"]),
        _Obj("c", ["nightly"]),
    ]
    result = filter_by_tags(objs, TagFilter(include=["etl"], exclude=["dev"]))
    assert [o.name for o in result] == ["a"]


def test_describe_filter_all():
    assert describe_filter(TagFilter()) == "TagFilter(all)"


def test_describe_filter_include_exclude():
    desc = describe_filter(TagFilter(include=["prod"], exclude=["debug"]))
    assert "include=prod" in desc
    assert "exclude=debug" in desc
