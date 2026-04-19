import pytest
from pipewatch.runner import RunResult
from pipewatch.pattern import (
    PatternRule, check_pattern, check_all_patterns,
    any_triggered, format_pattern_results,
)


def _result(stdout="", stderr=""):
    return RunResult(
        command="echo test",
        returncode=0,
        stdout=stdout,
        stderr=stderr,
        duration=0.1,
        timed_out=False,
    )


def test_match_found_in_stdout():
    r = _result(stdout="ERROR: something bad")
    rule = PatternRule(pattern="ERROR", match_on="stdout")
    pr = check_pattern(r, rule)
    assert pr.matched is True
    assert pr.triggered is True


def test_no_match_not_triggered():
    r = _result(stdout="all good")
    rule = PatternRule(pattern="ERROR", match_on="stdout")
    pr = check_pattern(r, rule)
    assert pr.matched is False
    assert pr.triggered is False


def test_invert_triggers_when_not_matched():
    r = _result(stdout="all good")
    rule = PatternRule(pattern="SUCCESS", match_on="stdout", invert=True)
    pr = check_pattern(r, rule)
    assert pr.matched is False
    assert pr.triggered is True


def test_invert_does_not_trigger_when_matched():
    r = _result(stdout="SUCCESS: done")
    rule = PatternRule(pattern="SUCCESS", match_on="stdout", invert=True)
    pr = check_pattern(r, rule)
    assert pr.matched is True
    assert pr.triggered is False


def test_match_on_stderr():
    r = _result(stderr="WARN: low disk")
    rule = PatternRule(pattern="WARN", match_on="stderr")
    pr = check_pattern(r, rule)
    assert pr.matched is True


def test_excerpt_populated_on_match():
    r = _result(stdout="prefix ERROR: oops suffix")
    rule = PatternRule(pattern="ERROR")
    pr = check_pattern(r, rule)
    assert "ERROR" in pr.excerpt


def test_check_all_patterns_returns_one_per_rule():
    r = _result(stdout="ERROR found")
    rules = [PatternRule(pattern="ERROR"), PatternRule(pattern="WARN")]
    results = check_all_patterns(r, rules)
    assert len(results) == 2


def test_any_triggered_true():
    r = _result(stdout="ERROR")
    rules = [PatternRule(pattern="ERROR"), PatternRule(pattern="WARN")]
    results = check_all_patterns(r, rules)
    assert any_triggered(results) is True


def test_any_triggered_false():
    r = _result(stdout="all good")
    rules = [PatternRule(pattern="ERROR"), PatternRule(pattern="WARN")]
    results = check_all_patterns(r, rules)
    assert any_triggered(results) is False


def test_format_includes_label():
    r = _result(stdout="ERROR")
    rule = PatternRule(pattern="ERROR", label="error-check")
    results = [check_pattern(r, rule)]
    out = format_pattern_results(results)
    assert "error-check" in out
    assert "TRIGGERED" in out
