"""Tests for pipewatch.digest."""
import pytest
from pipewatch.history import HistoryEntry
from pipewatch.digest import build_digest, format_digest, DigestSection


def _entry(success=True, duration=10.0, timed_out=False, tags=None):
    return HistoryEntry(
        timestamp="2024-01-01T00:00:00",
        command="echo hi",
        success=success,
        duration=duration,
        timed_out=timed_out,
        exit_code=0 if success else 1,
        tags=tags or [],
    )


def test_build_digest_all_section():
    entries = [_entry(), _entry(success=False)]
    digest = build_digest(entries)
    assert len(digest.sections) == 1
    assert digest.sections[0].label == "all"
    assert digest.sections[0].total == 2


def test_build_digest_success_rate():
    entries = [_entry(), _entry(), _entry(success=False)]
    digest = build_digest(entries)
    assert abs(digest.sections[0].success_rate - 2 / 3) < 0.001


def test_build_digest_empty():
    digest = build_digest([])
    assert digest.sections[0].total == 0
    assert digest.sections[0].success_rate == 0.0


def test_build_digest_group_by_tag():
    entries = [
        _entry(tags=["etl"]),
        _entry(tags=["etl"], success=False),
        _entry(tags=["api"]),
    ]
    digest = build_digest(entries, group_by_tag=True)
    labels = {s.label for s in digest.sections}
    assert labels == {"etl", "api"}


def test_build_digest_group_untagged():
    entries = [_entry(), _entry(tags=["etl"])]
    digest = build_digest(entries, group_by_tag=True)
    labels = {s.label for s in digest.sections}
    assert "untagged" in labels


def test_to_dict_keys():
    section = DigestSection(label="all", total=5, success_rate=0.8, avg_duration=3.5, timeouts=1)
    d = section.to_dict()
    assert set(d.keys()) == {"label", "total", "success_rate", "avg_duration", "timeouts"}


def test_format_digest_ok():
    entries = [_entry(), _entry()]
    digest = build_digest(entries)
    out = format_digest(digest)
    assert "[OK]" in out
    assert "all" in out


def test_format_digest_fail():
    entries = [_entry(success=False)]
    digest = build_digest(entries)
    out = format_digest(digest)
    assert "[FAIL]" in out


def test_format_digest_multiple_sections():
    entries = [_entry(tags=["a"]), _entry(tags=["b"], success=False)]
    digest = build_digest(entries, group_by_tag=True)
    out = format_digest(digest)
    assert "a" in out and "b" in out
