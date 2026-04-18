"""CLI entry point for pipewatch."""
import argparse
import sys
from pathlib import Path

from pipewatch.config import load_config, PipewatchConfig
from pipewatch.runner import run_command
from pipewatch.watcher import watch
from pipewatch.alert import send_slack_alert


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipewatch",
        description="Monitor long-running pipeline jobs with Slack alerting.",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run and monitor")
    parser.add_argument(
        "--config", "-c",
        type=Path,
        default=Path("pipewatch.toml"),
        help="Path to config file (default: pipewatch.toml)",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=float,
        default=None,
        help="Timeout in seconds (overrides config)",
    )
    parser.add_argument(
        "--slack-webhook",
        default=None,
        help="Slack webhook URL (overrides config)",
    )
    parser.add_argument(
        "--only-on-failure",
        action="store_true",
        default=None,
        help="Only alert on failure (overrides config)",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    command = [c for c in (args.command or []) if c != "--"]
    if not command:
        parser.print_help()
        return 1

    # Load config, fall back to defaults if missing
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        config = PipewatchConfig()

    # CLI overrides
    if args.timeout is not None:
        config.timeout = args.timeout
    if args.slack_webhook is not None:
        config.slack_webhook = args.slack_webhook
    if args.only_on_failure is not None:
        config.only_on_failure = args.only_on_failure

    result = watch(command, config)

    status = "✅ success" if result.run_result.success else "❌ failed"
    print(f"[pipewatch] {status} in {result.run_result.duration:.2f}s", file=sys.stderr)

    if result.run_result.timed_out:
        print("[pipewatch] command timed out", file=sys.stderr)

    if config.slack_webhook:
        send_slack_alert(config, result.run_result)

    return 0 if result.run_result.success else 1


if __name__ == "__main__":
    sys.exit(main())
