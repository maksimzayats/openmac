from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from openmac._internal.applescript.runner import AppleScriptRunner


def test_run_rejects_empty_script() -> None:
    runner = AppleScriptRunner()

    with pytest.raises(ValueError, match=r"AppleScript cannot be empty\."):
        runner.run("   ")


def test_run_raises_runtime_error_when_subprocess_fails() -> None:
    runner = AppleScriptRunner()

    with patch("openmac._internal.runner.subprocess.run", side_effect=OSError):
        with pytest.raises(RuntimeError, match="Failed to execute AppleScript"):
            runner.run("return 1")


def test_run_raises_runtime_error_on_non_zero_exit_with_stderr() -> None:
    runner = AppleScriptRunner()
    completed_process = SimpleNamespace(
        returncode=1,
        stdout="",
        stderr="script failed",
    )

    with patch("openmac._internal.runner.subprocess.run", return_value=completed_process):
        with pytest.raises(RuntimeError, match="script failed"):
            runner.run("return 1")


def test_run_raises_runtime_error_on_non_zero_exit_without_stderr() -> None:
    runner = AppleScriptRunner()
    completed_process = SimpleNamespace(
        returncode=1,
        stdout="",
        stderr="",
    )

    with patch("openmac._internal.runner.subprocess.run", return_value=completed_process):
        with pytest.raises(RuntimeError, match=r"AppleScript execution failed with exit code 1\."):
            runner.run("return 1")


def test_run_returns_stdout_without_trailing_newline() -> None:
    runner = AppleScriptRunner()
    completed_process = SimpleNamespace(
        returncode=0,
        stdout="ok\n",
        stderr="",
    )

    with patch("openmac._internal.runner.subprocess.run", return_value=completed_process):
        assert runner.run("return 1") == "ok"
