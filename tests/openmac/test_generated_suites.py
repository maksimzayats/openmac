from __future__ import annotations

import importlib
import inspect
from typing import Any, cast

import pytest

from openmac.chrome.suites import ChromiumSuite, StandardSuite as ChromeStandardSuite
from openmac.finder.suites import (
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
    "openmac.chrome.suites.standard_suite",
    "openmac.chrome.suites.chromium_suite",
    "openmac.finder.suites.standard_suite",
    "openmac.finder.suites.finder_basics_suite",
    "openmac.finder.suites.finder_items_suite",
    "openmac.finder.suites.containers_and_folders_suite",
    "openmac.finder.suites.files_suite",
    "openmac.finder.suites.window_classes_suite",
    "openmac.finder.suites.legacy_suite",
    "openmac.finder.suites.type_definitions_suite",
    "openmac.finder.suites.enumerations_suite",
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


def _required_arguments(method: Any) -> tuple[list[object], dict[str, object]]:
    positional_args: list[object] = []
    keyword_args: dict[str, object] = {}
    signature = inspect.signature(method)

    for parameter in signature.parameters.values():
        if parameter.name == "self" or parameter.default is not inspect.Signature.empty:
            continue
        if parameter.kind in {
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        }:
            positional_args.append(object())
            continue
        if parameter.kind is inspect.Parameter.KEYWORD_ONLY:
            keyword_args[parameter.name] = object()

    return (positional_args, keyword_args)


@pytest.mark.parametrize("module_name", GENERATED_MODULES)
def test_generated_suite_modules_import(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert hasattr(module, "SUITE_META")


@pytest.mark.parametrize("suite_class", SUITE_CLASSES)
def test_generated_suite_command_methods_raise_not_implemented(suite_class: type[object]) -> None:
    suite_instance = suite_class()
    command_methods = [
        method
        for _, method in inspect.getmembers(suite_class, predicate=inspect.isfunction)
        if not method.__name__.startswith("_")
    ]

    commands = cast("tuple[object, ...]", cast("Any", suite_class).COMMANDS)
    assert len(command_methods) == len(commands)
    for method in command_methods:
        positional_args, keyword_args = _required_arguments(method)
        with pytest.raises(NotImplementedError):
            method(suite_instance, *positional_args, **keyword_args)
