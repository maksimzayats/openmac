from __future__ import annotations

import importlib
from typing import Any, Final, cast, get_args, get_origin

import pytest
from pydantic import TypeAdapter

import openmac._internal.sdef.types as sdef_types
from openmac._internal.sdef.base import SDEFClass, SDEFCommand
from openmac.chrome.sdef.suites.chromium.commands import ExecuteCommand as ChromiumExecuteCommand
from openmac.chrome.sdef.suites.standard.commands import (
    CountCommand as ChromeCountCommand,
    ExistsCommand as ChromeExistsCommand,
    QuitCommand as ChromeQuitCommand,
)
from openmac.finder.sdef.suites.finder_basics.commands import SortCommand as FinderSortCommand

SUITE_PACKAGES: Final[tuple[tuple[str, str], ...]] = (
    ("openmac.chrome.sdef.suites", "standard"),
    ("openmac.chrome.sdef.suites", "chromium"),
    ("openmac.finder.sdef.suites", "standard"),
    ("openmac.finder.sdef.suites", "finder_basics"),
    ("openmac.finder.sdef.suites", "finder_items"),
    ("openmac.finder.sdef.suites", "containers_and_folders"),
    ("openmac.finder.sdef.suites", "files"),
    ("openmac.finder.sdef.suites", "window_classes"),
    ("openmac.finder.sdef.suites", "legacy"),
    ("openmac.finder.sdef.suites", "type_definitions"),
    ("openmac.finder.sdef.suites", "enumerations"),
)

BASE_SUBMODULES: Final[tuple[str, ...]] = (
    "meta",
    "classes",
    "enumerations",
    "value_types",
    "commands",
)

CLASS_EXTENSION_MODULES: Final[tuple[str, ...]] = (
    "openmac.chrome.sdef.suites.chromium.class_extensions",
    "openmac.finder.sdef.suites.legacy.class_extensions",
)

GENERATED_MODULES: Final[list[str]] = [
    f"{package_root}.{suite_name}.{submodule_name}"
    for package_root, suite_name in SUITE_PACKAGES
    for submodule_name in BASE_SUBMODULES
] + list(CLASS_EXTENSION_MODULES)

COMMAND_MODULES: Final[list[str]] = [
    f"{package_root}.{suite_name}.commands" for package_root, suite_name in SUITE_PACKAGES
]

ROOT_SUITES_MODULES_WITH_REMOVED_EXPORTS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    (
        "openmac.chrome.sdef.suites",
        ("StandardSuite", "ChromiumSuite"),
    ),
    (
        "openmac.finder.sdef.suites",
        (
            "StandardSuite",
            "FinderBasicsSuite",
            "FinderItemsSuite",
            "ContainersAndFoldersSuite",
            "FilesSuite",
            "WindowClassesSuite",
            "LegacySuite",
            "TypeDefinitionsSuite",
            "EnumerationsSuite",
        ),
    ),
)

SUITE_PACKAGE_MODULES_WITH_REMOVED_EXPORTS: Final[tuple[tuple[str, str], ...]] = (
    ("openmac.chrome.sdef.suites.standard", "StandardSuite"),
    ("openmac.chrome.sdef.suites.chromium", "ChromiumSuite"),
    ("openmac.finder.sdef.suites.standard", "StandardSuite"),
    ("openmac.finder.sdef.suites.finder_basics", "FinderBasicsSuite"),
    ("openmac.finder.sdef.suites.finder_items", "FinderItemsSuite"),
    ("openmac.finder.sdef.suites.containers_and_folders", "ContainersAndFoldersSuite"),
    ("openmac.finder.sdef.suites.files", "FilesSuite"),
    ("openmac.finder.sdef.suites.window_classes", "WindowClassesSuite"),
    ("openmac.finder.sdef.suites.legacy", "LegacySuite"),
    ("openmac.finder.sdef.suites.type_definitions", "TypeDefinitionsSuite"),
    ("openmac.finder.sdef.suites.enumerations", "EnumerationsSuite"),
)

CROSS_SUITE_ALIAS_MODULES: Final[tuple[str, ...]] = (
    "openmac.chrome.sdef.suites.standard.classes",
    "openmac.finder.sdef.suites.finder_basics.classes",
    "openmac.finder.sdef.suites.finder_items.classes",
    "openmac.finder.sdef.suites.window_classes.classes",
    "openmac.finder.sdef.suites.legacy.classes",
    "openmac.finder.sdef.suites.type_definitions.classes",
)

CROSS_SUITE_ALIAS_FIELDS: Final[tuple[tuple[str, str, str, str], ...]] = (
    (
        "openmac.chrome.sdef.suites.standard.classes",
        "Window",
        "active_tab",
        "ChromiumTabType",
    ),
    (
        "openmac.finder.sdef.suites.finder_basics.classes",
        "Application",
        "startup_disk",
        "ContainersAndFoldersDiskType",
    ),
    (
        "openmac.finder.sdef.suites.finder_basics.classes",
        "Application",
        "desktop",
        "ContainersAndFoldersDesktopObjectType",
    ),
    (
        "openmac.finder.sdef.suites.finder_basics.classes",
        "Application",
        "trash",
        "ContainersAndFoldersTrashObjectType",
    ),
    (
        "openmac.finder.sdef.suites.finder_basics.classes",
        "Application",
        "home",
        "ContainersAndFoldersFolderType",
    ),
    (
        "openmac.finder.sdef.suites.finder_basics.classes",
        "Application",
        "computer_container",
        "ContainersAndFoldersComputerObjectType",
    ),
    (
        "openmac.finder.sdef.suites.finder_basics.classes",
        "Application",
        "finder_preferences",
        "TypeDefinitionsPreferencesType",
    ),
    (
        "openmac.finder.sdef.suites.finder_items.classes",
        "Item",
        "icon",
        "TypeDefinitionsIconFamilyType",
    ),
    (
        "openmac.finder.sdef.suites.window_classes.classes",
        "FinderWindow",
        "icon_view_options",
        "TypeDefinitionsIconViewOptionsType",
    ),
    (
        "openmac.finder.sdef.suites.window_classes.classes",
        "FinderWindow",
        "list_view_options",
        "TypeDefinitionsListViewOptionsType",
    ),
    (
        "openmac.finder.sdef.suites.window_classes.classes",
        "FinderWindow",
        "column_view_options",
        "TypeDefinitionsColumnViewOptionsType",
    ),
    (
        "openmac.finder.sdef.suites.legacy.classes",
        "ApplicationProcess",
        "application_file",
        "FilesApplicationFileType",
    ),
    (
        "openmac.finder.sdef.suites.type_definitions.classes",
        "Preferences",
        "window",
        "WindowClassesPreferencesWindowType",
    ),
)

UNKNOWN_SPECIFIER_FIELDS: Final[tuple[tuple[str, str, str], ...]] = (
    ("openmac.finder.sdef.suites.window_classes.classes", "FinderWindow", "target"),
    ("openmac.finder.sdef.suites.finder_items.classes", "Item", "information_window"),
)


def command_classes_from_module(module_name: str) -> list[type[SDEFCommand[object]]]:
    module = importlib.import_module(module_name)
    return [
        candidate
        for candidate in module.__dict__.values()
        if isinstance(candidate, type)
        and issubclass(candidate, SDEFCommand)
        and candidate is not SDEFCommand
    ]


def annotation_contains_specifier(annotation: object) -> bool:
    if annotation is sdef_types.Specifier:
        return True
    origin = get_origin(annotation)
    if origin is None:
        return False
    if origin is sdef_types.Specifier:
        return True
    return any(annotation_contains_specifier(argument) for argument in get_args(annotation))


def command_result_type_argument(command_class: type[object]) -> object:
    for candidate in command_class.__mro__:
        pydantic_meta: object = getattr(candidate, "__pydantic_generic_metadata__", None)
        if isinstance(pydantic_meta, dict) and pydantic_meta.get("origin") is SDEFCommand:
            args = pydantic_meta.get("args")
            if isinstance(args, tuple) and len(args) == 1:
                if args[0] is None:
                    return type(None)
                return args[0]

    for candidate in command_class.__mro__:
        for base in getattr(candidate, "__orig_bases__", ()):
            if get_origin(base) is SDEFCommand:
                args = get_args(base)
                if len(args) == 1:
                    return args[0]

    msg = f"Command class {command_class.__qualname__!r} is not parameterized as SDEFCommand[TResult]."
    raise AssertionError(msg)


@pytest.mark.parametrize("module_name", COMMAND_MODULES)
def test_generated_command_classes_are_parameterized(module_name: str) -> None:
    for command_class in command_classes_from_module(module_name):
        command_result_type_argument(command_class)


def test_generated_command_result_type_arguments_match_expected_mappings() -> None:
    assert command_result_type_argument(ChromeQuitCommand) is type(None)
    assert command_result_type_argument(ChromiumExecuteCommand) == Any
    assert command_result_type_argument(ChromeExistsCommand) is bool
    assert command_result_type_argument(ChromeCountCommand) is int
    assert command_result_type_argument(FinderSortCommand) == (
        sdef_types.Specifier[SDEFClass] | None
    )


@pytest.mark.parametrize("module_name", GENERATED_MODULES)
def test_generated_suite_submodules_import(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert module is not None


@pytest.mark.parametrize("module_name", COMMAND_MODULES)
def test_generated_suite_commands_are_not_callable(module_name: str) -> None:
    expected_bundle_id = (
        "com.google.Chrome" if module_name.startswith("openmac.chrome.") else "com.apple.finder"
    )
    command_classes = command_classes_from_module(module_name)
    for command_class in command_classes:
        assert issubclass(command_class, SDEFCommand)
        assert cast("Any", command_class).SDEF_META.bundle_id == expected_bundle_id
        assert "__call__" not in command_class.__dict__
        required_values = {
            field_name: object()
            for field_name, field_info in command_class.model_fields.items()
            if field_info.is_required()
        }
        command_instance = cast("Any", command_class).model_construct(**required_values)
        assert not callable(command_instance)


@pytest.mark.parametrize("module_name", COMMAND_MODULES)
def test_generated_command_parameter_meta_field_names_match_model_fields(module_name: str) -> None:
    for command_class in command_classes_from_module(module_name):
        for parameter_meta in cast("Any", command_class).SDEF_META.parameters:
            assert parameter_meta.field_name is not None
            assert parameter_meta.field_name in command_class.model_fields


@pytest.mark.parametrize("module_name", COMMAND_MODULES)
def test_generated_type_parameters_are_typed_as_specifier(module_name: str) -> None:
    for command_class in command_classes_from_module(module_name):
        for parameter_meta in cast("Any", command_class).SDEF_META.parameters:
            if parameter_meta.type != "type":
                continue
            assert parameter_meta.field_name is not None
            annotation = command_class.model_fields[parameter_meta.field_name].annotation
            assert annotation_contains_specifier(annotation)


@pytest.mark.parametrize(
    ("module_name", "removed_exports"),
    ROOT_SUITES_MODULES_WITH_REMOVED_EXPORTS,
)
def test_root_suite_package_inits_do_not_reexport(
    module_name: str,
    removed_exports: tuple[str, ...],
) -> None:
    module = importlib.import_module(module_name)
    assert "__all__" not in module.__dict__
    for removed_export in removed_exports:
        assert not hasattr(module, removed_export)


@pytest.mark.parametrize(
    ("module_name", "removed_export"),
    SUITE_PACKAGE_MODULES_WITH_REMOVED_EXPORTS,
)
def test_suite_package_inits_do_not_reexport(module_name: str, removed_export: str) -> None:
    module = importlib.import_module(module_name)
    assert "__all__" not in module.__dict__
    assert not hasattr(module, removed_export)


@pytest.mark.parametrize("module_name", CROSS_SUITE_ALIAS_MODULES)
def test_cross_suite_alias_modules_import(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert module is not None


@pytest.mark.parametrize("field_case", CROSS_SUITE_ALIAS_FIELDS)
def test_cross_suite_alias_runtime_field_annotations_rebuild_to_specifier(
    field_case: tuple[str, str, str, str],
) -> None:
    module_name, class_name, field_name, expected_alias_type = field_case
    module = importlib.import_module(module_name)
    model_class = cast("Any", getattr(module, class_name))
    annotation = model_class.model_fields[field_name].annotation
    assert get_origin(annotation) is sdef_types.Specifier
    type_args = get_args(annotation)
    assert len(type_args) == 1
    assert issubclass(type_args[0], SDEFClass)
    assert expected_alias_type in model_class.__annotations__[field_name]


@pytest.mark.parametrize("field_case", CROSS_SUITE_ALIAS_FIELDS)
def test_cross_suite_class_field_annotations_use_alias_tokens(
    field_case: tuple[str, str, str, str],
) -> None:
    module_name, class_name, field_name, expected_annotation = field_case
    module = importlib.import_module(module_name)
    model_class = getattr(module, class_name)
    assert model_class.__annotations__[field_name] == f"sdef_types.Specifier[{expected_annotation}]"
    assert model_class.__annotations__[field_name] != "sdef_types.Specifier[SDEFClass]"


@pytest.mark.parametrize(("module_name", "class_name", "field_name"), UNKNOWN_SPECIFIER_FIELDS)
def test_unknown_specifier_fields_fallback_to_sdef_class(
    module_name: str,
    class_name: str,
    field_name: str,
) -> None:
    module = importlib.import_module(module_name)
    model_class = cast("Any", getattr(module, class_name))
    annotation = model_class.model_fields[field_name].annotation
    assert get_origin(annotation) is sdef_types.Specifier
    assert get_args(annotation) == (SDEFClass,)
    assert model_class.__annotations__[field_name] == "sdef_types.Specifier[SDEFClass]"


def test_cross_suite_alias_field_still_validates_specifier_strings() -> None:
    module = importlib.import_module("openmac.chrome.sdef.suites.standard.classes")
    model_class = cast("Any", module.Window)
    annotation = model_class.model_fields["active_tab"].annotation
    assert get_origin(annotation) is sdef_types.Specifier
    adapter = TypeAdapter(annotation)
    assert adapter.validate_python("tab 1 of window 1") == sdef_types.Specifier("tab 1 of window 1")
