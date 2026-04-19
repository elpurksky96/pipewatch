"""Filter alerts based on label/tag rules and severity conditions."""

from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.label import LabelSet, parse_labels


@dataclass
class AlertFilter:
    required_labels: LabelSet = field(default_factory=lambda: LabelSet({}))
    min_duration: Optional[float] = None  # seconds
    only_on_timeout: bool = False
    only_on_failure: bool = False


def parse_alert_filter(
    labels: Optional[str] = None,
    min_duration: Optional[float] = None,
    only_on_timeout: bool = False,
    only_on_failure: bool = False,
) -> AlertFilter:
    label_set = parse_labels(labels or "")
    return AlertFilter(
        required_labels=label_set,
        min_duration=min_duration,
        only_on_timeout=only_on_timeout,
        only_on_failure=only_on_failure,
    )


def should_alert(entry, alert_filter: AlertFilter) -> bool:
    """Return True if the entry passes the alert filter and an alert should fire."""
    if alert_filter.only_on_timeout and not getattr(entry, "timed_out", False):
        return False

    if alert_filter.only_on_failure:
        if getattr(entry, "success", True):
            return False

    if alert_filter.min_duration is not None:
        duration = getattr(entry, "duration", 0.0) or 0.0
        if duration < alert_filter.min_duration:
            return False

    entry_labels = getattr(entry, "labels", None)
    if entry_labels is not None and alert_filter.required_labels.as_dict():
        if not alert_filter.required_labels.matches(entry_labels):
            return False

    return True


def describe_filter(f: AlertFilter) -> str:
    parts = []
    if f.only_on_failure:
        parts.append("failures only")
    if f.only_on_timeout:
        parts.append("timeouts only")
    if f.min_duration is not None:
        parts.append(f"duration >= {f.min_duration}s")
    label_dict = f.required_labels.as_dict()
    if label_dict:
        kv = ", ".join(f"{k}={v}" for k, v in label_dict.items())
        parts.append(f"labels: {kv}")
    return "; ".join(parts) if parts else "no filters"
