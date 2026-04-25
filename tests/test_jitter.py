"""Tests for pipewatch.jitter."""

import pytest
from pipewatch.jitter import detect_jitter, format_jitter, JitterResult


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _uniform(value: float, n: int = 10) -> list:
    """All durations identical → stddev == 0."""
    return [value] * n


def _spread(base: float, delta: float, n: int = 10) -> list:
    """Alternating high/low values to produce predictable variance."""
    return [base + (delta if i % 2 == 0 else -delta) for i in range(n)]


# ---------------------------------------------------------------------------
# detect_jitter
# ---------------------------------------------------------------------------

def test_returns_none_when_too_few_samples():
    result = detect_jitter("cmd", [1.0, 2.0, 3.0], min_samples=5)
    assert result is None


def test_returns_none_when_mean_is_zero():
    result = detect_jitter("cmd", [0.0] * 6)
    assert result is None


def test_stable_durations_not_jittery():
    durations = _uniform(10.0)
    result = detect_jitter("cmd", durations, threshold=0.5)
    assert result is not None
    assert result.is_jittery is False
    assert result.cv == pytest.approx(0.0)
    assert result.stddev == pytest.approx(0.0)


def test_high_variance_is_jittery():
    # CV = stddev / mean; with alternating 1 and 9, mean=5, stddev=4 → CV=0.8
    durations = _spread(5.0, 4.0, n=10)
    result = detect_jitter("cmd", durations, threshold=0.5)
    assert result is not None
    assert result.is_jittery is True
    assert result.cv > 0.5


def test_custom_threshold_respected():
    # CV ~0.8; with threshold=0.9 it should NOT be flagged
    durations = _spread(5.0, 4.0, n=10)
    result = detect_jitter("cmd", durations, threshold=0.9)
    assert result is not None
    assert result.is_jittery is False


def test_sample_count_matches_input():
    durations = _uniform(5.0, n=7)
    result = detect_jitter("cmd", durations, min_samples=5)
    assert result is not None
    assert result.sample_count == 7


def test_threshold_stored_on_result():
    durations = _uniform(3.0)
    result = detect_jitter("cmd", durations, threshold=0.25)
    assert result.threshold == 0.25


def test_command_stored_on_result():
    durations = _uniform(2.0)
    result = detect_jitter("my-pipeline", durations)
    assert result.command == "my-pipeline"


# ---------------------------------------------------------------------------
# format_jitter
# ---------------------------------------------------------------------------

def test_format_jitter_stable_label():
    durations = _uniform(10.0)
    result = detect_jitter("cmd", durations)
    text = format_jitter(result)
    assert "stable" in text
    assert "cmd" in text


def test_format_jitter_jittery_label():
    durations = _spread(5.0, 4.0, n=10)
    result = detect_jitter("cmd", durations, threshold=0.5)
    text = format_jitter(result)
    assert "JITTERY" in text
