from __future__ import annotations

from pathlib import Path

import pytest

from tools.sdef.models import Command
from tools.sdef.parser import load_sdef

FIXTURE_PATH = Path(__file__).resolve().parents[3] / "tools" / "sdef" / "suite.sdef"
CHROME_SDEF_PATH = (
    Path(__file__).resolve().parents[3] / "src" / "openmac" / "chrome" / "chrome.sdef"
)
FINDER_SDEF_PATH = (
    Path(__file__).resolve().parents[3] / "src" / "openmac" / "finder" / "finder.sdef"
)
APP_SDEF_DIR = Path(__file__).resolve().parent / "captured_apps_sdef"
APP_SDEF_PATHS = sorted(APP_SDEF_DIR.glob("*.sdef"))
CHROMIUM_APP_SDEF_NAMES = {"google_chrome.sdef", "google_chrome_beta.sdef", "microsoft_edge.sdef"}


def _find_command(dictionary_title: str, command_name: str, fixture_path: Path) -> Command:
    dictionary = load_sdef(fixture_path)

    assert dictionary.title == dictionary_title

    for suite in dictionary.suites:
        for command in suite.commands:
            if command.name == command_name:
                return command

    pytest.fail(f"Missing command {command_name!r} in fixture {fixture_path.name}")


def test_captured_app_sdef_files_are_discovered() -> None:
    assert APP_SDEF_DIR.is_dir()
    assert APP_SDEF_PATHS


@pytest.mark.parametrize("fixture_path", APP_SDEF_PATHS, ids=lambda path: path.name)
def test_load_sdef_parses_all_captured_app_sdefs(fixture_path: Path) -> None:
    dictionary = load_sdef(fixture_path)
    assert dictionary.suites


def test_load_sdef_parses_repository_suite_fixture() -> None:
    save_command = _find_command("Dictionary", "save", FIXTURE_PATH)
    open_command = _find_command("Dictionary", "open", FIXTURE_PATH)

    assert save_command.access_groups
    assert save_command.access_groups[0].identifier == "*"
    assert open_command.direct_parameters
    assert open_command.direct_parameters[0].type is None
    assert open_command.direct_parameters[0].type_elements
    assert open_command.direct_parameters[0].type_elements[0].type == "file"
    assert open_command.direct_parameters[0].type_elements[0].list == "yes"


@pytest.mark.parametrize(
    "fixture_path",
    [path for path in APP_SDEF_PATHS if path.name in CHROMIUM_APP_SDEF_NAMES],
    ids=lambda path: path.name,
)
def test_load_sdef_parses_captured_chromium_app_sdefs(fixture_path: Path) -> None:
    save_command = _find_command("Dictionary", "save", fixture_path)
    open_command = _find_command("Dictionary", "open", fixture_path)

    assert save_command.access_groups
    assert save_command.access_groups[0].identifier == "*"
    assert open_command.direct_parameters
    assert open_command.direct_parameters[0].type_elements
    assert open_command.direct_parameters[0].type_elements[0].type == "file"


def test_load_sdef_parses_iwork_value_type_and_documentation() -> None:
    dictionary = load_sdef(APP_SDEF_DIR / "keynote.sdef")

    assert any(suite.value_types for suite in dictionary.suites)
    assert any(command.documentation for suite in dictionary.suites for command in suite.commands)


def test_load_sdef_parses_outlook_accessor_and_in_properties() -> None:
    dictionary = load_sdef(APP_SDEF_DIR / "microsoft_outlook.sdef")

    assert any(
        element.accessors
        for suite in dictionary.suites
        for class_ in suite.classes
        for element in class_.elements
    )
    assert any(
        property_.in_properties == "no"
        for suite in dictionary.suites
        for class_ in suite.classes
        for property_ in class_.properties
    )


def test_load_sdef_parses_xcode_requires_access_and_documentation() -> None:
    dictionary = load_sdef(APP_SDEF_DIR / "xcode.sdef")

    assert any(
        direct_parameter.requires_access
        for suite in dictionary.suites
        for command in suite.commands
        for direct_parameter in command.direct_parameters
    )
    assert any(command.documentation for suite in dictionary.suites for command in suite.commands)
    assert any(class_.documentation for suite in dictionary.suites for class_ in suite.classes)


def test_load_sdef_parses_repository_chrome_sdef() -> None:
    dictionary = load_sdef(CHROME_SDEF_PATH)

    assert dictionary.suites
    assert [suite.name for suite in dictionary.suites if suite.name]


def test_load_sdef_parses_repository_finder_sdef() -> None:
    dictionary = load_sdef(FINDER_SDEF_PATH)

    assert dictionary.suites
    assert [suite.name for suite in dictionary.suites if suite.name]


def test_load_sdef_rejects_unknown_fields_in_strict_mode(tmp_path: Path) -> None:
    sdef_path = tmp_path / "unknown-field.sdef"
    sdef_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<dictionary title="Dictionary">
  <suite name="Strict Suite" code="Strt">
    <command name="save" code="save" unsupported="value">
      <direct-parameter type="specifier"/>
    </command>
  </suite>
</dictionary>
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Failed to validate SDEF XML") as exc_info:
        load_sdef(sdef_path)

    assert str(sdef_path) in str(exc_info.value)


def test_load_sdef_rejects_malformed_xml(tmp_path: Path) -> None:
    sdef_path = tmp_path / "malformed.sdef"
    sdef_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<dictionary title="Dictionary">
  <suite name="Bad Suite">
</dictionary>
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Failed to parse SDEF XML") as exc_info:
        load_sdef(sdef_path)

    assert str(sdef_path) in str(exc_info.value)
