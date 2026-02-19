from __future__ import annotations

import subprocess  # noqa: S404 - required to execute osascript
from dataclasses import dataclass
from typing import Final

OSASCRIPT_EXECUTABLE: Final[str] = "/usr/bin/osascript"
OSASCRIPT_EXECUTE_FLAG: Final[str] = "-e"


@dataclass(slots=True, frozen=True)
class AppleScriptExecutor:
    executable: str = OSASCRIPT_EXECUTABLE

    def execute(self, script: str) -> str:
        if not script.strip():
            raise ValueError("AppleScript cannot be empty.")

        try:
            completed_process = subprocess.run(  # noqa: S603
                [self.executable, OSASCRIPT_EXECUTE_FLAG, script],
                capture_output=True,
                check=False,
                text=True,
            )
        except OSError as error:
            msg = f"Failed to execute AppleScript using {self.executable!r}."
            raise RuntimeError(msg) from error

        if completed_process.returncode != 0:
            stderr = completed_process.stderr.strip()
            if stderr:
                msg = f"AppleScript execution failed with exit code {completed_process.returncode}: {stderr}"
            else:
                msg = f"AppleScript execution failed with exit code {completed_process.returncode}."
            raise RuntimeError(msg)

        return completed_process.stdout.rstrip("\n")
