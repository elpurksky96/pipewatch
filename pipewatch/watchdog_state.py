"""Persistent last-seen timestamps for watchdog tracking."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional


_DEFAULT_PATH = Path(".pipewatch") / "watchdog_state.json"


def _load(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save(state: Dict[str, str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))


def get_last_seen(command: str, path: Path = _DEFAULT_PATH) -> Optional[str]:
    """Return ISO timestamp of last recorded run, or None."""
    return _load(path).get(command)


def record_seen(command: str, path: Path = _DEFAULT_PATH) -> str:
    """Record the current UTC time as the last-seen timestamp for *command*."""
    state = _load(path)
    ts = datetime.now(timezone.utc).isoformat()
    state[command] = ts
    _save(state, path)
    return ts


def clear_seen(command: str, path: Path = _DEFAULT_PATH) -> bool:
    """Remove the last-seen entry for *command*. Returns True if it existed."""
    state = _load(path)
    if command in state:
        del state[command]
        _save(state, path)
        return True
    return False


def all_seen(path: Path = _DEFAULT_PATH) -> Dict[str, str]:
    """Return a copy of all last-seen entries."""
    return dict(_load(path))
