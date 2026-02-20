from __future__ import annotations

import types
from typing import Any, cast
from unittest.mock import patch

import pytest

from openmac._internal.applescript.executor import AppleScriptExecutor
from openmac._internal.applescript.runner import AppleScriptSDEFCommandRunner
from openmac._internal.sdef import SDEFCommand
from openmac.chrome.sdef.suites.standard.commands import QuitCommand as ChromeQuitCommand


def test_run_raw_executes_builder_script_and_returns_stdout() -> None:
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
        assert runner.run_raw(command) == "ok"

    builder_class_mock.assert_called_once_with(command)
    builder_class_mock.return_value.build_script.assert_called_once_with()
    execute_mock.assert_called_once_with(executor, "generated-script")


def test_run_executes_builder_script_and_returns_none_for_none_result() -> None:
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
            return_value="ignored",
        ) as execute_mock,
        patch("openmac._internal.applescript.runner.loads", autospec=True) as loads_mock,
    ):
        builder_class_mock.return_value.build_script.return_value = "generated-script"
        assert runner.run(command) is None

    builder_class_mock.assert_called_once_with(command)
    builder_class_mock.return_value.build_script.assert_called_once_with()
    execute_mock.assert_called_once_with(executor, "generated-script")
    loads_mock.assert_not_called()


def test_run_loads_typed_result_from_stdout() -> None:
    class IntResultCommand(SDEFCommand[int]):
        pass

    executor = AppleScriptExecutor()
    runner = AppleScriptSDEFCommandRunner(executor=executor)
    command = IntResultCommand.model_validate({})

    with (
        patch.object(
            AppleScriptSDEFCommandRunner,
            "run_raw",
            autospec=True,
            return_value="123",
        ) as run_raw_mock,
        patch(
            "openmac._internal.applescript.runner.loads",
            autospec=True,
            return_value=123,
        ) as loads_mock,
    ):
        assert runner.run(command) == 123

    run_raw_mock.assert_called_once()
    loads_mock.assert_called_once_with("123", expected=int)


def test_run_uses_orig_bases_fallback_when_present() -> None:
    orig_bases_command_class = cast(
        "type[SDEFCommand[object]]",
        type("OrigBasesCommand", (SDEFCommand,), {}),
    )
    cast("Any", orig_bases_command_class).__orig_bases__ = (
        types.GenericAlias(SDEFCommand, ()),
        types.GenericAlias(SDEFCommand, int),
    )

    executor = AppleScriptExecutor()
    runner = AppleScriptSDEFCommandRunner(executor=executor)
    command = orig_bases_command_class.model_validate({})

    with (
        patch.object(
            SDEFCommand,
            "__pydantic_generic_metadata__",
            {"origin": SDEFCommand, "args": (), "parameters": ()},
        ),
        patch.object(
            AppleScriptSDEFCommandRunner,
            "run_raw",
            autospec=True,
            return_value="123",
        ),
        patch(
            "openmac._internal.applescript.runner.loads",
            autospec=True,
            return_value=123,
        ),
    ):
        assert runner.run(command) == 123


def test_run_raises_value_error_when_command_is_not_parameterized() -> None:
    untyped_command_class = cast(
        "type[SDEFCommand[object]]",
        type("UntypedCommand", (SDEFCommand,), {}),
    )

    executor = AppleScriptExecutor()
    runner = AppleScriptSDEFCommandRunner(executor=executor)
    command = untyped_command_class.model_validate({})

    with pytest.raises(ValueError, match=r"must inherit from SDEFCommand\[TResult\]"):
        runner.run(command)
