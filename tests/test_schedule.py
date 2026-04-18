"""Tests for pipewatch.schedule."""

import pytest
from datetime import datetime
from pipewatch.schedule import ScheduleConfig, is_due, describe


def _dt(minute=0, hour=9, day=1, month=1, weekday=0):
    # weekday: 0=Monday
    # Find a date matching the weekday (2024-01-01 is Monday)
    base = datetime(2024, month, day, hour, minute)
    return base


def test_wildcard_always_matches():
    cfg = ScheduleConfig(cron="* * * * *")
    assert is_due(cfg, datetime(2024, 6, 15, 12, 30))


def test_exact_minute_match():
    cfg = ScheduleConfig(cron="30 * * * *")
    assert is_due(cfg, datetime(2024, 1, 1, 10, 30))
    assert not is_due(cfg, datetime(2024, 1, 1, 10, 31))


def test_step_expression():
    cfg = ScheduleConfig(cron="*/15 * * * *")
    assert is_due(cfg, datetime(2024, 1, 1, 10, 0))
    assert is_due(cfg, datetime(2024, 1, 1, 10, 15))
    assert is_due(cfg, datetime(2024, 1, 1, 10, 30))
    assert is_due(cfg, datetime(2024, 1, 1, 10, 45))
    assert not is_due(cfg, datetime(2024, 1, 1, 10, 7))


def test_range_expression():
    cfg = ScheduleConfig(cron="0 9-17 * * *")
    assert is_due(cfg, datetime(2024, 1, 1, 9, 0))
    assert is_due(cfg, datetime(2024, 1, 1, 17, 0))
    assert not is_due(cfg, datetime(2024, 1, 1, 8, 0))
    assert not is_due(cfg, datetime(2024, 1, 1, 18, 0))


def test_comma_list():
    cfg = ScheduleConfig(cron="0 8,12,18 * * *")
    assert is_due(cfg, datetime(2024, 1, 1, 8, 0))
    assert is_due(cfg, datetime(2024, 1, 1, 12, 0))
    assert not is_due(cfg, datetime(2024, 1, 1, 10, 0))


def test_invalid_cron_raises():
    cfg = ScheduleConfig(cron="* * *")
    with pytest.raises(ValueError, match="Invalid cron"):
        is_due(cfg)


def test_describe():
    cfg = ScheduleConfig(cron="0 9 * * *", timezone="America/New_York")
    result = describe(cfg)
    assert "0 9 * * *" in result
    assert "America/New_York" in result


def test_default_timezone():
    cfg = ScheduleConfig(cron="* * * * *")
    assert cfg.timezone == "UTC"
