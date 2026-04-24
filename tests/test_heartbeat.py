"""Tests for pipewatch.heartbeat."""

import os
import time

import pytest

from pipewatch.heartbeat import (
    HeartbeatEntry,
    StalenessAlert,
    check_heartbeats,
    format_heartbeat_report,
    from_dict,
    record_heartbeat,
    to_dict,
)


@pytest.fixture()
def hb_path(tmp_path):
    return str(tmp_path / "heartbeats.json")


def test_roundtrip_dict():
    entry = HeartbeatEntry(command="etl", last_seen=1_000_000.0, interval_seconds=1800)
    assert from_dict(to_dict(entry)).command == "etl"
    assert from_dict(to_dict(entry)).last_seen == 1_000_000.0
    assert from_dict(to_dict(entry)).interval_seconds == 1800


def test_load_missing_file_returns_empty(hb_path):
    alerts = check_heartbeats(hb_path, now=time.time())
    assert alerts == []


def test_record_creates_entry(hb_path):
    record_heartbeat(hb_path, "my-job", interval_seconds=60)
    # just recorded — should not be overdue
    alerts = check_heartbeats(hb_path, now=time.time())
    assert alerts == []


def test_overdue_entry_triggers_alert(hb_path):
    past = time.time() - 7200  # 2 hours ago
    from pipewatch.heartbeat import HeartbeatEntry, _save_all

    _save_all(
        hb_path,
        {
            "slow-job": HeartbeatEntry(
                command="slow-job", last_seen=past, interval_seconds=3600
            )
        },
    )
    alerts = check_heartbeats(hb_path, now=time.time())
    assert len(alerts) == 1
    assert alerts[0].command == "slow-job"
    assert alerts[0].seconds_overdue > 3500


def test_healthy_entry_no_alert(hb_path):
    now = time.time()
    from pipewatch.heartbeat import HeartbeatEntry, _save_all

    _save_all(
        hb_path,
        {
            "fast-job": HeartbeatEntry(
                command="fast-job", last_seen=now - 10, interval_seconds=3600
            )
        },
    )
    alerts = check_heartbeats(hb_path, now=now)
    assert alerts == []


def test_multiple_entries_only_stale_alerted(hb_path):
    now = time.time()
    from pipewatch.heartbeat import HeartbeatEntry, _save_all

    _save_all(
        hb_path,
        {
            "ok": HeartbeatEntry(command="ok", last_seen=now - 10, interval_seconds=3600),
            "stale": HeartbeatEntry(
                command="stale", last_seen=now - 7200, interval_seconds=3600
            ),
        },
    )
    alerts = check_heartbeats(hb_path, now=now)
    assert len(alerts) == 1
    assert alerts[0].command == "stale"


def test_format_report_no_alerts():
    assert format_heartbeat_report([]) == "All heartbeats healthy."


def test_format_report_with_alert():
    alert = StalenessAlert(
        command="nightly", last_seen=0.0, interval_seconds=3600, seconds_overdue=600.0
    )
    report = format_heartbeat_report([alert])
    assert "nightly" in report
    assert "10.0 min" in report
