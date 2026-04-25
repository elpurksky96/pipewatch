"""Tests for pipewatch.drift."""

import pytest
from pipewatch.drift import DriftResult, detect_drift, format_drift


CMD = "etl-job"


def test_no_drift_when_identical():
    snap = {"DB_HOST": "localhost", "WORKERS": "4"}
    result = detect_drift(CMD, snap, snap.copy())
    assert not result.has_drift
    assert result.drift_count == 0


def test_added_key_detected():
    baseline = {"A": "1"}
    current = {"A": "1", "B": "2"}
    result = detect_drift(CMD, baseline, current)
    assert result.added == {"B": "2"}
    assert not result.removed
    assert not result.changed
    assert result.has_drift


def test_removed_key_detected():
    baseline = {"A": "1", "B": "2"}
    current = {"A": "1"}
    result = detect_drift(CMD, baseline, current)
    assert result.removed == {"B": "2"}
    assert not result.added
    assert not result.changed


def test_changed_value_detected():
    baseline = {"A": "old"}
    current = {"A": "new"}
    result = detect_drift(CMD, baseline, current)
    assert result.changed == {"A": ("old", "new")}
    assert not result.added
    assert not result.removed


def test_drift_count_aggregates_all_categories():
    baseline = {"A": "1", "B": "2", "C": "3"}
    current = {"A": "changed", "C": "3", "D": "4"}
    result = detect_drift(CMD, baseline, current)
    # A changed, B removed, D added
    assert result.drift_count == 3


def test_ignore_keys_excluded_from_diff():
    baseline = {"A": "1", "SECRET": "old"}
    current = {"A": "1", "SECRET": "new"}
    result = detect_drift(CMD, baseline, current, ignore_keys=["SECRET"])
    assert not result.has_drift


def test_ignore_keys_does_not_affect_other_keys():
    baseline = {"A": "1", "SKIP": "x"}
    current = {"A": "2", "SKIP": "y"}
    result = detect_drift(CMD, baseline, current, ignore_keys=["SKIP"])
    assert result.changed == {"A": ("1", "2")}


def test_format_drift_no_changes():
    snap = {"X": "1"}
    result = detect_drift(CMD, snap, snap.copy())
    output = format_drift(result)
    assert "No drift" in output
    assert CMD in output


def test_format_drift_shows_added():
    result = detect_drift(CMD, {}, {"NEW_KEY": "hello"})
    output = format_drift(result)
    assert "+ NEW_KEY=hello" in output


def test_format_drift_shows_removed():
    result = detect_drift(CMD, {"OLD_KEY": "bye"}, {})
    output = format_drift(result)
    assert "- OLD_KEY=bye" in output


def test_format_drift_shows_changed():
    result = detect_drift(CMD, {"K": "v1"}, {"K": "v2"})
    output = format_drift(result)
    assert "~ K" in output
    assert "v1" in output
    assert "v2" in output
