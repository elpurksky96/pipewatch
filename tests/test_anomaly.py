"""Tests for pipewatch.anomaly module."""

import pytest
from pipewatch.anomaly import detect_anomaly, format_anomaly, AnomalyResult


DURATIONS_NORMAL = [10.0, 10.5, 9.8, 10.2, 10.1, 9.9]  # tight cluster around 10s


def test_returns_none_when_too_few_samples():
    result = detect_anomaly("cmd", 10.0, [10.0, 10.0, 10.0], min_samples=5)
    assert result is None


def test_returns_none_when_stddev_zero():
    result = detect_anomaly("cmd", 10.0, [10.0, 10.0, 10.0, 10.0, 10.0], min_samples=5)
    assert result is None


def test_normal_duration_not_anomaly():
    result = detect_anomaly("cmd", 10.3, DURATIONS_NORMAL, threshold=2.5)
    assert result is not None
    assert result.is_anomaly is False
    assert result.z_score < 2.5


def test_very_long_duration_is_anomaly():
    result = detect_anomaly("cmd", 60.0, DURATIONS_NORMAL, threshold=2.5)
    assert result is not None
    assert result.is_anomaly is True
    assert result.direction == "slow"


def test_very_short_duration_is_anomaly():
    result = detect_anomaly("cmd", 0.1, DURATIONS_NORMAL, threshold=2.5)
    assert result is not None
    assert result.is_anomaly is True
    assert result.direction == "fast"


def test_result_fields_populated():
    result = detect_anomaly("my-pipeline", 10.0, DURATIONS_NORMAL)
    assert result is not None
    assert result.command == "my-pipeline"
    assert result.duration == 10.0
    assert result.mean == pytest.approx(10.083, abs=0.01)
    assert result.stddev > 0
    assert result.threshold == 2.5


def test_custom_threshold_lower():
    # With threshold=0.1, almost anything should be an anomaly
    result = detect_anomaly("cmd", 10.6, DURATIONS_NORMAL, threshold=0.1)
    assert result is not None
    assert result.is_anomaly is True


def test_format_anomaly_anomaly_label():
    result = AnomalyResult(
        command="etl",
        duration=60.0,
        mean=10.0,
        stddev=0.5,
        z_score=100.0,
        is_anomaly=True,
        threshold=2.5,
    )
    text = format_anomaly(result)
    assert "ANOMALY" in text
    assert "etl" in text
    assert "slow" in text


def test_format_anomaly_normal_label():
    result = AnomalyResult(
        command="etl",
        duration=10.1,
        mean=10.0,
        stddev=0.5,
        z_score=0.2,
        is_anomaly=False,
        threshold=2.5,
    )
    text = format_anomaly(result)
    assert "normal" in text
    assert "ANOMALY" not in text
