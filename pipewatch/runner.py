"""Run a shell command and monitor its execution."""

import subprocess
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RunResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False

    @property
    def success(self) -> bool:
        return self.returncode == 0 and not self.timed_out


def run_command(
    command: str,
    timeout: Optional[int] = None,
    shell: bool = True,
) -> RunResult:
    """Execute a shell command and return a RunResult."""
    start = time.monotonic()
    timed_out = False

    try:
        proc = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        returncode = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = -1
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")

    duration = time.monotonic() - start

    return RunResult(
        command=command,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        duration_seconds=round(duration, 3),
        timed_out=timed_out,
    )
