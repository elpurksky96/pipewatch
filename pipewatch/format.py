"""Formatting helpers for pipewatch output and Slack messages."""
from pipewatch.runner import RunResult


MAX_STDERR_LINES = 20


def format_duration(seconds: float) -> str:
    """Return a human-readable duration string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins}m {secs}s"


def format_status(result: RunResult) -> str:
    """Return a short status string for a run result."""
    if result.timed_out:
        return "timed out"
    if result.success:
        return "succeeded"
    return f"failed (exit {result.returncode})"


def truncate_stderr(stderr: str, max_lines: int = MAX_STDERR_LINES) -> str:
    """Truncate stderr to the last N lines."""
    if not stderr:
        return ""
    lines = stderr.rstrip().splitlines()
    if len(lines) <= max_lines:
        return stderr.rstrip()
    omitted = len(lines) - max_lines
    tail = "\n".join(lines[-max_lines:])
    return f"[... {omitted} lines omitted ...]\n{tail}"


def format_summary(result: RunResult) -> str:
    """Return a multi-line summary suitable for terminal or Slack."""
    lines = [
        f"Command : {' '.join(result.command)}",
        f"Status  : {format_status(result)}",
        f"Duration: {format_duration(result.duration)}",
    ]
    if result.stderr:
        lines.append("Stderr (tail):")
        lines.append(truncate_stderr(result.stderr))
    return "\n".join(lines)
