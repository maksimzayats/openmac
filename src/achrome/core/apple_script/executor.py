import subprocess
from dataclasses import dataclass
from typing import Protocol


@dataclass(kw_only=True, slots=True)
class AppleScriptExecutor:
    """Utility for running AppleScript via osascript."""

    def run_applescript(self, script: str, args: list[str] | None = None) -> str:
        """Run AppleScript via osascript and returns stdout (stripped).

        Uses argv to avoid quoting/escaping bugs.
        """
        if args is None:
            args = []

        proc = subprocess.run(  # noqa: S603
            ["osascript", "-l", "AppleScript", "-", *args],  # noqa: S607
            check=False,
            input=script,
            text=True,
            capture_output=True,
        )

        if proc.returncode != 0:
            raise AppleScriptError(
                proc.stderr.strip() or "AppleScript failed with no stderr output."
            )

        return proc.stdout.rstrip("\n")


class AppleScriptError(RuntimeError):
    """Raised when AppleScript execution fails (non-zero exit code)."""


class AppleScriptExecutorLike(Protocol):
    """Protocol for AppleScript executor implementations."""

    def run_applescript(self, script: str, args: list[str] | None = None) -> str:
        """Run AppleScript and return stdout."""
