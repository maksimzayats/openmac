from __future__ import annotations

from types import NoneType

import pytest

from openmac._internal.applescript import serializer
from openmac._internal.applescript.script_builder import AppleScriptSDEFScriptBuilder
from openmac._internal.sdef import SDEFCommand, meta as sdef_meta
from openmac.apps.chrome.sdef.suites.chromium.commands import GoBackCommand, ReloadCommand
from openmac.apps.chrome.sdef.suites.standard.commands import QuitCommand as ChromeQuitCommand
from openmac.apps.finder.sdef.suites.finder_items.commands import CleanUpCommand
from openmac.apps.finder.sdef.suites.standard.commands import (
    ActivateCommand,
    CountCommand,
    DuplicateCommand,
)


def test_build_script_for_command_without_arguments() -> None:
    command = ChromeQuitCommand.model_validate({})

    assert AppleScriptSDEFScriptBuilder(command).build_script() == (
        'tell application id "com.google.Chrome"\n    quit\nend tell'
    )


def test_build_script_with_direct_parameter_only() -> None:
    command = ReloadCommand.model_validate({"direct_parameter": "tab 1 of window 1"})

    assert AppleScriptSDEFScriptBuilder(command).build_script() == (
        'tell application id "com.google.Chrome"\n    reload tab 1 of window 1\nend tell'
    )


def test_build_script_with_parameter_aliases_and_spaces() -> None:
    command = DuplicateCommand.model_validate({
        "direct_parameter": "file 1 of home",
        "to": "desktop",
        "routing suppressed": True,
        "exact copy": False,
    })

    assert AppleScriptSDEFScriptBuilder(command).build_script() == (
        'tell application id "com.apple.finder"\n'
        "    duplicate file 1 of home to desktop routing suppressed true exact copy false\n"
        "end tell"
    )


def test_build_script_with_command_name_containing_spaces() -> None:
    command = GoBackCommand.model_validate({"direct_parameter": "tab 1 of window 1"})

    assert AppleScriptSDEFScriptBuilder(command).build_script() == (
        'tell application id "com.google.Chrome"\n    go back tab 1 of window 1\nend tell'
    )


def test_build_script_omits_optional_parameters_when_none() -> None:
    command = DuplicateCommand.model_validate({"direct_parameter": "file 1 of home"})

    assert AppleScriptSDEFScriptBuilder(command).build_script() == (
        'tell application id "com.apple.finder"\n    duplicate file 1 of home\nend tell'
    )


def test_build_script_omits_optional_named_parameter_when_none() -> None:
    command = CleanUpCommand.model_validate({"direct_parameter": "window 1", "by": None})

    assert AppleScriptSDEFScriptBuilder(command).build_script() == (
        'tell application id "com.apple.finder"\n    clean up window 1\nend tell'
    )


def test_build_script_missing_required_parameter_fails_fast() -> None:
    command = CountCommand.model_construct(direct_parameter="window 1")

    with pytest.raises(ValueError, match=r"requires parameter 'each'.*model value is missing"):
        AppleScriptSDEFScriptBuilder(command).build_script()


def test_build_script_missing_required_direct_parameter_fails_fast() -> None:
    command = ReloadCommand.model_construct()

    with pytest.raises(ValueError, match=r"expects direct_parameter.*model value is missing"):
        AppleScriptSDEFScriptBuilder(command).build_script()


def test_build_script_missing_required_direct_parameter_value_fails_fast() -> None:
    command = ReloadCommand.model_construct(direct_parameter=None)

    with pytest.raises(ValueError, match=r"requires direct_parameter, but value is missing"):
        AppleScriptSDEFScriptBuilder(command).build_script()


def test_build_script_missing_required_parameter_value_fails_fast() -> None:
    command = CountCommand.model_construct(direct_parameter="window 1", each=None)

    with pytest.raises(ValueError, match=r"requires parameter 'each'.*value is missing"):
        AppleScriptSDEFScriptBuilder(command).build_script()


def test_build_script_omits_optional_direct_parameter_when_none() -> None:
    command = ActivateCommand.model_validate({})

    assert AppleScriptSDEFScriptBuilder(command).build_script() == (
        'tell application id "com.apple.finder"\n    activate\nend tell'
    )


def test_build_script_type_parameter_is_rendered_as_raw_identifier() -> None:
    command = CountCommand.model_validate({
        "direct_parameter": "window 1",
        "each": "folder",
    })

    script = AppleScriptSDEFScriptBuilder(command).build_script()

    assert " each folder\n" in script
    assert ' each "folder"\n' not in script


class BrokenFieldNameMetaCommand(SDEFCommand[NoneType]):
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


class BrokenDirectParameterMetaCommand(SDEFCommand[NoneType]):
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


class BrokenParameterReferenceMetaCommand(SDEFCommand[NoneType]):
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


def test_build_script_fails_fast_when_parameter_field_name_missing() -> None:
    command = BrokenFieldNameMetaCommand.model_validate({"with_value": "x"})

    with pytest.raises(ValueError, match=r"missing field_name metadata"):
        AppleScriptSDEFScriptBuilder(command).build_script()


def test_build_script_fails_fast_when_direct_parameter_field_missing() -> None:
    command = BrokenDirectParameterMetaCommand.model_validate({})

    with pytest.raises(ValueError, match=r"expects direct_parameter.*field is missing"):
        AppleScriptSDEFScriptBuilder(command).build_script()


def test_build_script_fails_fast_when_parameter_field_reference_is_unknown() -> None:
    command = BrokenParameterReferenceMetaCommand.model_validate({"with_value": "x"})

    with pytest.raises(ValueError, match=r"references unknown model field 'unknown_field'"):
        AppleScriptSDEFScriptBuilder(command).build_script()


def test_build_script_uses_serializer_for_bundle_id() -> None:
    command = ChromeQuitCommand.model_validate({})

    script = AppleScriptSDEFScriptBuilder(command).build_script()

    assert script.startswith(
        f"tell application id {serializer.dumps(command.SDEF_META.bundle_id)}\n",
    )
