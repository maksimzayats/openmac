from __future__ import annotations

from pathlib import Path

import pytest

from tools.sdef.parser import load_sdef

FIXTURE_PATH = Path(__file__).resolve().parents[3] / "tools" / "sdef" / "suite.sdef"
APP_SDEF_DIR = Path(__file__).resolve().parent / "captured_apps_sdef"
APP_SDEF_NAMES = (
    "developer.sdef",
    "google_chrome.sdef",
    "google_chrome_beta.sdef",
    "iterm.sdef",
    "keynote.sdef",
    "microsoft_edge.sdef",
    "microsoft_excel.sdef",
    "microsoft_outlook.sdef",
    "microsoft_word.sdef",
    "numbers.sdef",
    "pages.sdef",
    "safari.sdef",
    "spotify.sdef",
    "xcode.sdef",
)
CHROMIUM_APP_SDEFS = ("google_chrome.sdef", "google_chrome_beta.sdef", "microsoft_edge.sdef")


def test_captured_app_sdef_files_exist() -> None:
    assert APP_SDEF_DIR.is_dir()

    for fixture_name in APP_SDEF_NAMES:
        assert (APP_SDEF_DIR / fixture_name).is_file()


@pytest.mark.parametrize("fixture_name", CHROMIUM_APP_SDEFS)
def test_load_sdef_parses_captured_chromium_app_sdefs(fixture_name: str) -> None:
    dictionary = load_sdef(APP_SDEF_DIR / fixture_name)

    assert dictionary.title == "Dictionary"
    assert len(dictionary.suites) == 2

    save_command = None
    open_command = None

    for suite in dictionary.suites:
        for command in suite.commands:
            if command.name == "save":
                save_command = command
            if command.name == "open":
                open_command = command

    assert save_command is not None
    assert open_command is not None
    assert save_command.access_groups
    assert save_command.access_groups[0].identifier == "*"
    assert open_command.direct_parameters
    assert open_command.direct_parameters[0].type_elements
    assert open_command.direct_parameters[0].type_elements[0].type == "file"


def test_load_sdef_parses_repository_suite_fixture() -> None:
    dictionary = load_sdef(FIXTURE_PATH)

    assert dictionary.title == "Dictionary"
    assert len(dictionary.suites) == 2

    save_command = None
    open_command = None

    for suite in dictionary.suites:
        for command in suite.commands:
            if command.name == "save":
                save_command = command
            if command.name == "open":
                open_command = command

    assert save_command is not None
    assert open_command is not None
    assert save_command.access_groups
    assert save_command.access_groups[0].identifier == "*"

    assert open_command.direct_parameters
    assert open_command.direct_parameters[0].type is None
    assert open_command.direct_parameters[0].type_elements
    assert open_command.direct_parameters[0].type_elements[0].type == "file"
    assert open_command.direct_parameters[0].type_elements[0].list == "yes"


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
