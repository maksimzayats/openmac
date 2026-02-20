from __future__ import annotations

import pytest

from openmac._internal.applescript.executor import AppleScriptExecutor

pytestmark = pytest.mark.integration


def test_execute_runs_real_osascript_and_returns_stdout_without_trailing_newline(
    integration_executor: AppleScriptExecutor,
) -> None:
    assert integration_executor.execute('return "openmac-integration"') == "openmac-integration"


def test_execute_raises_runtime_error_for_invalid_applescript(
    integration_executor: AppleScriptExecutor,
) -> None:
    with pytest.raises(RuntimeError, match="AppleScript execution failed with exit code"):
        integration_executor.execute('return "unterminated')
