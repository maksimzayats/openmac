from __future__ import annotations

import importlib
from typing import Any, cast

import pytest

from openmac._internal.models import SDEFCommand
from openmac.chrome.sdef.suites import ChromiumSuite, StandardSuite as ChromeStandardSuite
from openmac.finder.sdef.suites import (
    ContainersAndFoldersSuite,
    EnumerationsSuite,
    FilesSuite,
    FinderBasicsSuite,
    FinderItemsSuite,
    LegacySuite,
    StandardSuite as FinderStandardSuite,
    TypeDefinitionsSuite,
    WindowClassesSuite,
)

GENERATED_MODULES = [
    "openmac.chrome.suites",
    "openmac.chrome.sdef.suites.standard_suite",
    "openmac.chrome.sdef.suites.chromium_suite",
    "openmac.finder.suites",
    "openmac.finder.sdef.suites.standard_suite",
    "openmac.finder.sdef.suites.finder_basics_suite",
    "openmac.finder.sdef.suites.finder_items_suite",
    "openmac.finder.sdef.suites.containers_and_folders_suite",
    "openmac.finder.sdef.suites.files_suite",
    "openmac.finder.sdef.suites.window_classes_suite",
    "openmac.finder.sdef.suites.legacy_suite",
    "openmac.finder.sdef.suites.type_definitions_suite",
    "openmac.finder.sdef.suites.enumerations_suite",
]

SUITE_CLASSES = [
    ChromeStandardSuite,
    ChromiumSuite,
    FinderStandardSuite,
    FinderBasicsSuite,
    FinderItemsSuite,
    ContainersAndFoldersSuite,
    FilesSuite,
    WindowClassesSuite,
    LegacySuite,
    TypeDefinitionsSuite,
    EnumerationsSuite,
]


@pytest.mark.parametrize("module_name", GENERATED_MODULES)
def test_generated_suite_modules_import(module_name: str) -> None:
    module = importlib.import_module(module_name)
    if module_name.endswith(".suites"):
        assert hasattr(module, "__all__")
    else:
        assert hasattr(module, "SUITE_META")


@pytest.mark.parametrize("suite_class", SUITE_CLASSES)
def test_generated_suite_commands_raise_not_implemented(suite_class: type[object]) -> None:
    commands = cast("tuple[type[SDEFCommand], ...]", cast("Any", suite_class).COMMANDS)
    for command_class in commands:
        assert issubclass(command_class, SDEFCommand)
        required_values = {
            field_name: object()
            for field_name, field_info in command_class.model_fields.items()
            if field_info.is_required()
        }
        command_instance = cast("Any", command_class).model_construct(**required_values)
        with pytest.raises(NotImplementedError):
            command_instance()
