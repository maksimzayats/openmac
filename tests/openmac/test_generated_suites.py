from __future__ import annotations

import importlib
from typing import Any, Final, cast

import pytest

from openmac._internal.sdef.base import SDEFCommand

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


@pytest.mark.parametrize("module_name", GENERATED_MODULES)
def test_generated_suite_submodules_import(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert module is not None


@pytest.mark.parametrize("module_name", COMMAND_MODULES)
def test_generated_suite_commands_raise_not_implemented(module_name: str) -> None:
    module = importlib.import_module(module_name)
    expected_bundle_id = (
        "com.google.Chrome" if module_name.startswith("openmac.chrome.") else "com.apple.finder"
    )
    command_classes = [
        candidate
        for candidate in module.__dict__.values()
        if isinstance(candidate, type)
        and issubclass(candidate, SDEFCommand)
        and candidate is not SDEFCommand
    ]
    for command_class in command_classes:
        assert issubclass(command_class, SDEFCommand)
        assert cast("Any", command_class).SDEF_META.bundle_id == expected_bundle_id
        required_values = {
            field_name: object()
            for field_name, field_info in command_class.model_fields.items()
            if field_info.is_required()
        }
        command_instance = cast("Any", command_class).model_construct(**required_values)
        with pytest.raises(NotImplementedError):
            command_instance()


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
