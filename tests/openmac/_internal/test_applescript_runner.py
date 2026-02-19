from __future__ import annotations

from unittest.mock import patch

from openmac._internal.applescript.executor import AppleScriptExecutor
from openmac._internal.applescript.runner import AppleScriptSDEFCommandRunner
from openmac.chrome.sdef.suites.standard.commands import QuitCommand as ChromeQuitCommand


def test_run_executes_builder_script_and_returns_result() -> None:
    executor = AppleScriptExecutor()
    runner = AppleScriptSDEFCommandRunner(executor=executor)
    command = ChromeQuitCommand.model_validate({})

    with (
        patch(
            "openmac._internal.applescript.runner.AppleScriptSDEFScriptBuilder",
            autospec=True,
        ) as builder_class_mock,
        patch.object(
            AppleScriptExecutor,
            "execute",
            autospec=True,
            return_value="ok",
        ) as execute_mock,
    ):
        builder_class_mock.return_value.build_script.return_value = "generated-script"
        assert runner.run(command) == "ok"

    builder_class_mock.assert_called_once_with(command)
    builder_class_mock.return_value.build_script.assert_called_once_with()
    execute_mock.assert_called_once_with(executor, "generated-script")
