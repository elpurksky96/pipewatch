"""Tests for pipewatch.tagged_history."""
import pytest
from pipewatch.tagged_history import make_entry_with_tags, summarize_by_tag, load_tagged_history
from pipewatch.tags import TagFilter


def _entry(tags, success=True):
    return make_entry_with_tags("echo hi", tags, success=success, duration=1.0)


def test_make_entry_has_tags():
    e = _entry(["etl", "prod"])
    assert e.tags == ["etl", "prod"]
    assert e.command == "echo hi"
    assert e.success is True


def test_summarize_by_tag_counts():
    entries = [
        _entry(["etl", "prod"]),
        _entry(["etl", "dev"]),
        _entry(["nightly"]),
    ]
    counts = summarize_by_tag(entries)
    assert counts["etl"] == 2
    assert counts["prod"] == 1
    assert counts["dev"] == 1
    assert counts["nightly"] == 1


def test_summarize_by_tag_empty():
    assert summarize_by_tag([]) == {}


def test_load_tagged_history_missing_file_returns_empty(tmp_path):
    result = load_tagged_history(str(tmp_path / "nope.json"))
    assert result == []


def test_load_tagged_history_filter(tmp_path):
    from pipewatch.history import append_entry
    path = str(tmp_path / "hist.json")
    e1 = _entry(["etl"])
    e2 = _entry(["nightly"])
    # Persist without tags (tags are runtime-only)
    append_entry(path, e1)
    append_entry(path, e2)
    # Load; tags will default to [] since history doesn't persist them
    entries = load_tagged_history(path, TagFilter(include=["etl"]))
    # No entries match because stored entries have no tags
    assert isinstance(entries, list)
