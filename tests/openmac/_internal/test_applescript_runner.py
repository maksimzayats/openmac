from __future__ import annotations

from typing import cast
from unittest.mock import patch

import pytest

from openmac._internal.applescript.executor import AppleScriptExecutor
from openmac._internal.applescript.runner import AppleScriptSDEFCommandRunner
from openmac._internal.sdef import SDEFCommand


class DemoCommand(SDEFCommand):
    value: int


class DemoRunner(AppleScriptSDEFCommandRunner):
    def _generate_applescript(self, command: SDEFCommand) -> str:
        return f"return {cast('DemoCommand', command).value}"


def test_run_executes_generated_script_and_returns_result() -> None:
    executor = AppleScriptExecutor()
    runner = DemoRunner(executor=executor)
    command = DemoCommand.model_validate({"value": 7})

    with patch.object(
        AppleScriptExecutor,
        "execute",
        autospec=True,
        return_value="ok",
    ) as execute_mock:
        assert runner.run(command) == "ok"

    execute_mock.assert_called_once_with(executor, "return 7")


def test_generate_applescript_is_required() -> None:
    runner = AppleScriptSDEFCommandRunner(executor=AppleScriptExecutor())
    command = DemoCommand.model_validate({"value": 1})

    with pytest.raises(NotImplementedError):
        runner._generate_applescript(command)
