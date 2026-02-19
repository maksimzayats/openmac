from __future__ import annotations

from types import SimpleNamespace
from typing import Final
from unittest.mock import patch

import pytest

from openmac._internal.applescript.executor import AppleScriptExecutor

SUBPROCESS_RUN_PATH: Final[str] = "openmac._internal.applescript.executor.subprocess.run"


def test_run_rejects_empty_script() -> None:
    executor = AppleScriptExecutor()

    with pytest.raises(ValueError, match=r"AppleScript cannot be empty\."):
        executor.run("   ")


def test_run_raises_runtime_error_when_subprocess_fails() -> None:
    executor = AppleScriptExecutor()

    with patch(SUBPROCESS_RUN_PATH, side_effect=OSError):
        with pytest.raises(RuntimeError, match="Failed to execute AppleScript"):
            executor.run("return 1")


def test_run_raises_runtime_error_on_non_zero_exit_with_stderr() -> None:
    executor = AppleScriptExecutor()
    completed_process = SimpleNamespace(
        returncode=1,
        stdout="",
        stderr="script failed",
    )

    with patch(SUBPROCESS_RUN_PATH, return_value=completed_process):
        with pytest.raises(RuntimeError, match="script failed"):
            executor.run("return 1")


def test_run_raises_runtime_error_on_non_zero_exit_without_stderr() -> None:
    executor = AppleScriptExecutor()
    completed_process = SimpleNamespace(
        returncode=1,
        stdout="",
        stderr="",
    )

    with patch(SUBPROCESS_RUN_PATH, return_value=completed_process):
        with pytest.raises(RuntimeError, match=r"AppleScript execution failed with exit code 1\."):
            executor.run("return 1")


def test_run_returns_stdout_without_trailing_newline() -> None:
    executor = AppleScriptExecutor()
    completed_process = SimpleNamespace(
        returncode=0,
        stdout="ok\n",
        stderr="",
    )

    with patch(SUBPROCESS_RUN_PATH, return_value=completed_process):
        assert executor.run("return 1") == "ok"
