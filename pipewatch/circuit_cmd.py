"""CLI subcommands for circuit breaker management."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipewatch.circuit_breaker import (
    DEFAULT_STATE_PATH,
    _load,
    load_state,
    reset_circuit,
)


def cmd_circuit_status(args: Any) -> int:
    path = Path(getattr(args, "state_path", DEFAULT_STATE_PATH))
    data = _load(path)
    if not data:
        print("No circuit breaker state recorded.")
        return 0
    for command, raw in sorted(data.items()):
        failures = raw.get("consecutive_failures", 0)
        tripped = raw.get("tripped_at")
        state = load_state(command, path)
        status = "OPEN" if state.is_open() else ("HALF-OPEN" if state.is_half_open() else "CLOSED")
        print(f"{command}: {status} (failures={failures}, tripped_at={tripped})")
    return 0


def cmd_circuit_reset(args: Any) -> int:
    path = Path(getattr(args, "state_path", DEFAULT_STATE_PATH))
    command = getattr(args, "command", None)
    if command:
        reset_circuit(command, path)
        print(f"Circuit reset for: {command}")
    else:
        data = _load(path)
        for cmd in list(data.keys()):
            reset_circuit(cmd, path)
        print(f"Reset {len(data)} circuit(s).")
    return 0


def add_circuit_subparser(subparsers: Any) -> None:
    p = subparsers.add_parser("circuit", help="Manage circuit breakers")
    sub = p.add_subparsers(dest="circuit_cmd")

    p_status = sub.add_parser("status", help="Show circuit breaker states")
    p_status.set_defaults(func=cmd_circuit_status)

    p_reset = sub.add_parser("reset", help="Reset a tripped circuit")
    p_reset.add_argument("command", nargs="?", help="Command key (omit to reset all)")
    p_reset.set_defaults(func=cmd_circuit_reset)


def dispatch(args: Any) -> int:
    func = getattr(args, "func", None)
    if func is None:
        print("Usage: pipewatch circuit {status,reset}")
        return 1
    return func(args)
