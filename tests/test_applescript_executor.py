import subprocess

import pytest

from achrome.core.apple_script.executor import AppleScriptError, AppleScriptExecutor


def test_run_applescript_returns_stdout_without_newline(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["osascript"],
            returncode=0,
            stdout="hello\n",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    executor = AppleScriptExecutor()
    result = executor.run_applescript("return 1", args=["foo"])

    assert result == "hello"


def test_run_applescript_with_default_args(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["osascript"],
            returncode=0,
            stdout="value\n",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    executor = AppleScriptExecutor()
    result = executor.run_applescript("return 1")

    assert result == "value"


def test_run_applescript_raises_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["osascript"],
            returncode=1,
            stdout="",
            stderr="boom\n",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    executor = AppleScriptExecutor()
    with pytest.raises(AppleScriptError, match="boom"):
        executor.run_applescript("return 1", args=["foo"])


def test_run_applescript_raises_default_error_message(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["osascript"],
            returncode=1,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    executor = AppleScriptExecutor()
    with pytest.raises(AppleScriptError, match="no stderr output"):
        executor.run_applescript("return 1", args=["foo"])
