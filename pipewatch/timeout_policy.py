"""Timeout policy: define per-command timeout overrides and classify results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TimeoutPolicy:
    """Maps command patterns to timeout values (seconds) and escalation flags."""
    default_timeout: Optional[int] = None
    overrides: Dict[str, int] = field(default_factory=dict)
    warn_at_fraction: float = 0.8  # warn when elapsed >= fraction * timeout

    def resolve_timeout(self, command: str) -> Optional[int]:
        """Return the effective timeout for a given command string."""
        for pattern, seconds in self.overrides.items():
            if pattern in command:
                return seconds
        return self.default_timeout

    def warn_threshold(self, command: str) -> Optional[float]:
        t = self.resolve_timeout(command)
        if t is None:
            return None
        return t * self.warn_at_fraction


def parse_policy(raw: dict) -> TimeoutPolicy:
    """Build a TimeoutPolicy from a plain dict (e.g. loaded from config)."""
    return TimeoutPolicy(
        default_timeout=raw.get("default_timeout"),
        overrides={str(k): int(v) for k, v in raw.get("overrides", {}).items()},
        warn_at_fraction=float(raw.get("warn_at_fraction", 0.8)),
    )


def policy_to_dict(policy: TimeoutPolicy) -> dict:
    return {
        "default_timeout": policy.default_timeout,
        "overrides": dict(policy.overrides),
        "warn_at_fraction": policy.warn_at_fraction,
    }


def classify_duration(
    elapsed: float, command: str, policy: TimeoutPolicy
) -> str:
    """Return 'ok', 'warn', or 'exceeded' based on elapsed vs policy."""
    timeout = policy.resolve_timeout(command)
    if timeout is None:
        return "ok"
    if elapsed >= timeout:
        return "exceeded"
    warn = policy.warn_threshold(command)
    if warn is not None and elapsed >= warn:
        return "warn"
    return "ok"
