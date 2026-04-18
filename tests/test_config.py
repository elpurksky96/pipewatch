"""Tests for pipewatch configuration loader."""

import json
import os
import tempfile
import pytest

from pipewatch.config import PipewatchConfig, load_config, save_config


def test_default_config_values():
    config = PipewatchConfig()
    assert config.slack_webhook_url is None
    assert config.slack_channel is None
    assert config.alert_on_failure is True
    assert config.alert_on_success is False
    assert config.timeout_seconds is None
    assert config.job_name is None
    assert config.extra == {}


def test_from_dict_known_fields():
    data = {
        "slack_webhook_url": "https://hooks.slack.com/test",
        "slack_channel": "#alerts",
        "alert_on_failure": False,
        "timeout_seconds": 3600,
    }
    config = PipewatchConfig.from_dict(data)
    assert config.slack_webhook_url == "https://hooks.slack.com/test"
    assert config.slack_channel == "#alerts"
    assert config.alert_on_failure is False
    assert config.timeout_seconds == 3600


def test_from_dict_extra_fields():
    data = {"job_name": "etl-job", "custom_tag": "prod"}
    config = PipewatchConfig.from_dict(data)
    assert config.job_name == "etl-job"
    assert config.extra == {"custom_tag": "prod"}


def test_load_config_missing_file():
    config = load_config("/nonexistent/path/pipewatch.json")
    assert isinstance(config, PipewatchConfig)
    assert config.slack_webhook_url is None


def test_save_and_load_config_roundtrip():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = f.name
    try:
        original = PipewatchConfig(
            slack_webhook_url="https://hooks.slack.com/abc",
            slack_channel="#data",
            alert_on_success=True,
            timeout_seconds=1800,
            job_name="my-pipeline",
        )
        save_config(original, tmp_path)
        loaded = load_config(tmp_path)
        assert loaded.slack_webhook_url == original.slack_webhook_url
        assert loaded.slack_channel == original.slack_channel
        assert loaded.alert_on_success is True
        assert loaded.timeout_seconds == 1800
        assert loaded.job_name == "my-pipeline"
    finally:
        os.unlink(tmp_path)


def test_to_dict_includes_all_fields():
    config = PipewatchConfig(job_name="test", extra={"env": "staging"})
    d = config.to_dict()
    assert d["job_name"] == "test"
    assert d["env"] == "staging"
    assert "slack_webhook_url" in d
