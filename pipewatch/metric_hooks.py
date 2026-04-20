"""Hook integration: auto-record duration and success metrics after a run."""

from __future__ import annotations

import datetime
from typing import Optional

from pipewatch.metric import MetricPoint, save_metric
from pipewatch.watcher import WatchResult

_DEFAULT_PATH = ".pipewatch/metrics.jsonl"


def _now_iso() -> str:
    return datetime.datetime.utcnow().isoformat()


def record_run_metrics(
    result: WatchResult,
    command: str,
    path: str = _DEFAULT_PATH,
    extra_tags: Optional[dict] = None,
) -> None:
    """Save duration and success/failure as metric points."""
    tags = {"command": command}
    if extra_tags:
        tags.update(extra_tags)
    ts = _now_iso()

    duration_point = MetricPoint(
        command=command,
        name="duration_seconds",
        value=round(result.run_result.duration, 4),
        timestamp=ts,
        tags=tags,
    )
    save_metric(path, duration_point)

    success_value = 1.0 if result.run_result.success else 0.0
    success_point = MetricPoint(
        command=command,
        name="success",
        value=success_value,
        timestamp=ts,
        tags=tags,
    )
    save_metric(path, success_point)

    if result.run_result.timed_out:
        timeout_point = MetricPoint(
            command=command,
            name="timed_out",
            value=1.0,
            timestamp=ts,
            tags=tags,
        )
        save_metric(path, timeout_point)


def summarize_metric_hooks(path: str = _DEFAULT_PATH, command: Optional[str] = None) -> str:
    from pipewatch.metric import aggregate, filter_metrics, load_metrics

    pts = load_metrics(path)
    dur_pts = filter_metrics(pts, command=command, name="duration_seconds")
    suc_pts = filter_metrics(pts, command=command, name="success")

    if not dur_pts:
        return "No metric data recorded."

    dur_agg = aggregate(dur_pts)
    suc_agg = aggregate(suc_pts)
    rate = suc_agg.get("mean", 0.0) * 100 if suc_pts else 0.0
    return (
        f"Runs: {int(dur_agg['count'])} | "
        f"Avg duration: {dur_agg['mean']:.2f}s | "
        f"Success rate: {rate:.1f}%"
    )
