from __future__ import annotations

import subprocess  # noqa: S404
from unittest.mock import patch

import pytest
from openmac.core._internal.apple_scripts.runner import AppleScriptRunner


def test_run_executes_osascript_and_returns_output_without_trailing_newline() -> None:
    completed_process = subprocess.CompletedProcess(
        args=["/usr/bin/osascript", "-e", 'return "ok"'],
        returncode=0,
        stdout="ok\n",
        stderr="",
    )

    with patch(
        "achrome.core._internal.apple_script.subprocess.run",
        return_value=completed_process,
    ) as run_mock:
        result = AppleScriptRunner().run('return "ok"')

    assert result == "ok"
    run_mock.assert_called_once_with(
        ["/usr/bin/osascript", "-e", 'return "ok"'],
        capture_output=True,
        check=False,
        text=True,
    )


def test_run_raises_value_error_for_empty_script() -> None:
    with pytest.raises(ValueError, match=r"AppleScript cannot be empty\."):
        AppleScriptRunner().run("  \n\t")


def test_run_raises_runtime_error_when_osascript_returns_non_zero_code() -> None:
    completed_process = subprocess.CompletedProcess(
        args=["/usr/bin/osascript", "-e", "return 1"],
        returncode=1,
        stdout="",
        stderr="execution error\n",
    )

    with patch(
        "achrome.core._internal.apple_script.subprocess.run",
        return_value=completed_process,
    ):
        with pytest.raises(
            RuntimeError,
            match=r"AppleScript execution failed with exit code 1: execution error",
        ):
            AppleScriptRunner().run("return 1")


def test_run_raises_runtime_error_without_stderr_when_osascript_returns_non_zero_code() -> None:
    completed_process = subprocess.CompletedProcess(
        args=["/usr/bin/osascript", "-e", "return 1"],
        returncode=1,
        stdout="",
        stderr="",
    )

    with patch(
        "achrome.core._internal.apple_script.subprocess.run",
        return_value=completed_process,
    ):
        with pytest.raises(
            RuntimeError,
            match=r"AppleScript execution failed with exit code 1\.",
        ):
            AppleScriptRunner().run("return 1")


def test_run_raises_runtime_error_when_subprocess_launch_fails() -> None:
    with patch(
        "achrome.core._internal.apple_script.subprocess.run",
        side_effect=FileNotFoundError("missing executable"),
    ):
        with pytest.raises(
            RuntimeError,
            match=r"Failed to execute AppleScript using '/usr/bin/osascript'\.",
        ):
            AppleScriptRunner().run('return "ok"')
