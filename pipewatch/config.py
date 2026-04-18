"""Configuration loader for pipewatch."""

import os
import json
from dataclasses import dataclass, field
from typing import Optional

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.pipewatch.json")


@dataclass
class PipewatchConfig:
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    alert_on_failure: bool = True
    alert_on_success: bool = False
    timeout_seconds: Optional[int] = None
    job_name: Optional[str] = None
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "PipewatchConfig":
        known_fields = {
            "slack_webhook_url",
            "slack_channel",
            "alert_on_failure",
            "alert_on_success",
            "timeout_seconds",
            "job_name",
        }
        kwargs = {k: v for k, v in data.items() if k in known_fields}
        extra = {k: v for k, v in data.items() if k not in known_fields}
        return cls(**kwargs, extra=extra)

    def to_dict(self) -> dict:
        return {
            "slack_webhook_url": self.slack_webhook_url,
            "slack_channel": self.slack_channel,
            "alert_on_failure": self.alert_on_failure,
            "alert_on_success": self.alert_on_success,
            "timeout_seconds": self.timeout_seconds,
            "job_name": self.job_name,
            **self.extra,
        }


def load_config(path: str = DEFAULT_CONFIG_PATH) -> PipewatchConfig:
    """Load configuration from a JSON file, falling back to defaults."""
    if not os.path.exists(path):
        return PipewatchConfig()
    with open(path, "r") as f:
        data = json.load(f)
    return PipewatchConfig.from_dict(data)


def save_config(config: PipewatchConfig, path: str = DEFAULT_CONFIG_PATH) -> None:
    """Persist configuration to a JSON file."""
    with open(path, "w") as f:
        json.dump(config.to_dict(), f, indent=2)
