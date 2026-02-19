from __future__ import annotations

from unittest.mock import patch

import pytest

from openmac._internal.applescript import serializer
from openmac._internal.applescript.executor import AppleScriptExecutor
from openmac._internal.applescript.runner import AppleScriptSDEFCommandRunner
from openmac._internal.sdef import SDEFCommand, meta as sdef_meta
from openmac.chrome.sdef.suites.chromium.commands import GoBackCommand, ReloadCommand
from openmac.chrome.sdef.suites.standard.commands import QuitCommand as ChromeQuitCommand
from openmac.finder.sdef.suites.finder_items.commands import CleanUpCommand
from openmac.finder.sdef.suites.standard.commands import (
    ActivateCommand,
    CountCommand,
    DuplicateCommand,
)


def test_run_executes_generated_script_and_returns_result() -> None:
    executor = AppleScriptExecutor()
    runner = AppleScriptSDEFCommandRunner(executor=executor)
    command = ChromeQuitCommand.model_validate({})
    expected_script = 'tell application id "com.google.Chrome"\n    quit\nend tell'

    with patch.object(
        AppleScriptExecutor,
        "execute",
        autospec=True,
        return_value="ok",
    ) as execute_mock:
        assert runner.run(command) == "ok"

    execute_mock.assert_called_once_with(executor, expected_script)


def test_generate_applescript_for_command_without_arguments() -> None:
    runner = AppleScriptSDEFCommandRunner(executor=AppleScriptExecutor())
    command = ChromeQuitCommand.model_validate({})

    assert runner._generate_applescript(command) == (
        'tell application id "com.google.Chrome"\n    quit\nend tell'
    )


def test_generate_applescript_with_direct_parameter_only() -> None:
    runner = AppleScriptSDEFCommandRunner(executor=AppleScriptExecutor())
    command = ReloadCommand.model_validate({"direct_parameter": "tab 1 of window 1"})

    assert runner._generate_applescript(command) == (
        'tell application id "com.google.Chrome"\n    reload tab 1 of window 1\nend tell'
    )


def test_generate_applescript_with_parameter_aliases_and_spaces() -> None:
    runner = AppleScriptSDEFCommandRunner(executor=AppleScriptExecutor())
    command = DuplicateCommand.model_validate({
        "direct_parameter": "file 1 of home",
        "to": "desktop",
        "routing suppressed": True,
        "exact copy": False,
    })

    assert runner._generate_applescript(command) == (
        'tell application id "com.apple.finder"\n'
        "    duplicate file 1 of home to desktop routing suppressed true exact copy false\n"
        "end tell"
    )


def test_generate_applescript_with_command_name_containing_spaces() -> None:
    runner = AppleScriptSDEFCommandRunner(executor=AppleScriptExecutor())
    command = GoBackCommand.model_validate({"direct_parameter": "tab 1 of window 1"})

    assert runner._generate_applescript(command) == (
        'tell application id "com.google.Chrome"\n    go back tab 1 of window 1\nend tell'
    )


def test_generate_applescript_omits_optional_parameters_when_none() -> None:
    runner = AppleScriptSDEFCommandRunner(executor=AppleScriptExecutor())
    command = DuplicateCommand.model_validate({"direct_parameter": "file 1 of home"})

    assert runner._generate_applescript(command) == (
        'tell application id "com.apple.finder"\n    duplicate file 1 of home\nend tell'
    )


def test_generate_applescript_omits_optional_named_parameter_when_none() -> None:
    runner = AppleScriptSDEFCommandRunner(executor=AppleScriptExecutor())
    command = CleanUpCommand.model_validate({"direct_parameter": "window 1", "by": None})

    assert runner._generate_applescript(command) == (
        'tell application id "com.apple.finder"\n    clean up window 1\nend tell'
    )


def test_generate_applescript_missing_required_parameter_fails_fast() -> None:
    runner = AppleScriptSDEFCommandRunner(executor=AppleScriptExecutor())
    command = CountCommand.model_construct(direct_parameter="window 1")

    with pytest.raises(ValueError, match=r"requires parameter 'each'.*model value is missing"):
        runner._generate_applescript(command)


def test_generate_applescript_missing_required_direct_parameter_fails_fast() -> None:
    runner = AppleScriptSDEFCommandRunner(executor=AppleScriptExecutor())
    command = ReloadCommand.model_construct()

    with pytest.raises(ValueError, match=r"expects direct_parameter.*model value is missing"):
        runner._generate_applescript(command)


def test_generate_applescript_missing_required_direct_parameter_value_fails_fast() -> None:
    runner = AppleScriptSDEFCommandRunner(executor=AppleScriptExecutor())
    command = ReloadCommand.model_construct(direct_parameter=None)

    with pytest.raises(ValueError, match=r"requires direct_parameter, but value is missing"):
        runner._generate_applescript(command)


def test_generate_applescript_missing_required_parameter_value_fails_fast() -> None:
    runner = AppleScriptSDEFCommandRunner(executor=AppleScriptExecutor())
    command = CountCommand.model_construct(direct_parameter="window 1", each=None)

    with pytest.raises(ValueError, match=r"requires parameter 'each'.*value is missing"):
        runner._generate_applescript(command)


def test_generate_applescript_omits_optional_direct_parameter_when_none() -> None:
    runner = AppleScriptSDEFCommandRunner(executor=AppleScriptExecutor())
    command = ActivateCommand.model_validate({})

    assert runner._generate_applescript(command) == (
        'tell application id "com.apple.finder"\n    activate\nend tell'
    )


def test_generate_applescript_type_parameter_is_rendered_as_raw_identifier() -> None:
    runner = AppleScriptSDEFCommandRunner(executor=AppleScriptExecutor())
    command = CountCommand.model_validate({
        "direct_parameter": "window 1",
        "each": "folder",
    })

    script = runner._generate_applescript(command)

    assert " each folder\n" in script
    assert ' each "folder"\n' not in script


class BrokenFieldNameMetaCommand(SDEFCommand):
    SDEF_META = sdef_meta.CommandMeta(
        name="broken",
        code=None,
        description=None,
        hidden=None,
        bundle_id="com.example.app",
        direct_parameter_type=None,
        has_direct_parameter=False,
        direct_parameter_optional=None,
        parameters=(
            sdef_meta.ParameterMeta(
                name="with value",
                code=None,
                type="text",
                description=None,
                optional=False,
                hidden=None,
                requires_access=None,
                field_name=None,
            ),
        ),
        result=None,
        access_groups=(),
    )
    with_value: str


class BrokenDirectParameterMetaCommand(SDEFCommand):
    SDEF_META = sdef_meta.CommandMeta(
        name="broken direct",
        code=None,
        description=None,
        hidden=None,
        bundle_id="com.example.app",
        direct_parameter_type="specifier",
        has_direct_parameter=True,
        direct_parameter_optional=False,
        parameters=(),
        result=None,
        access_groups=(),
    )


class BrokenParameterReferenceMetaCommand(SDEFCommand):
    SDEF_META = sdef_meta.CommandMeta(
        name="broken parameter",
        code=None,
        description=None,
        hidden=None,
        bundle_id="com.example.app",
        direct_parameter_type=None,
        has_direct_parameter=False,
        direct_parameter_optional=None,
        parameters=(
            sdef_meta.ParameterMeta(
                name="with value",
                code=None,
                type="text",
                description=None,
                optional=False,
                hidden=None,
                requires_access=None,
                field_name="unknown_field",
            ),
        ),
        result=None,
        access_groups=(),
    )
    with_value: str


def test_generate_applescript_fails_fast_when_parameter_field_name_missing() -> None:
    runner = AppleScriptSDEFCommandRunner(executor=AppleScriptExecutor())
    command = BrokenFieldNameMetaCommand.model_validate({"with_value": "x"})

    with pytest.raises(ValueError, match=r"missing field_name metadata"):
        runner._generate_applescript(command)


def test_generate_applescript_fails_fast_when_direct_parameter_field_missing() -> None:
    runner = AppleScriptSDEFCommandRunner(executor=AppleScriptExecutor())
    command = BrokenDirectParameterMetaCommand.model_validate({})

    with pytest.raises(ValueError, match=r"expects direct_parameter.*field is missing"):
        runner._generate_applescript(command)


def test_generate_applescript_fails_fast_when_parameter_field_reference_is_unknown() -> None:
    runner = AppleScriptSDEFCommandRunner(executor=AppleScriptExecutor())
    command = BrokenParameterReferenceMetaCommand.model_validate({"with_value": "x"})

    with pytest.raises(ValueError, match=r"references unknown model field 'unknown_field'"):
        runner._generate_applescript(command)


def test_generate_applescript_script_uses_serializer_for_bundle_id() -> None:
    runner = AppleScriptSDEFCommandRunner(executor=AppleScriptExecutor())
    command = ChromeQuitCommand.model_validate({})

    script = runner._generate_applescript(command)

    assert script.startswith(
        f"tell application id {serializer.dumps(command.SDEF_META.bundle_id)}\n",
    )
