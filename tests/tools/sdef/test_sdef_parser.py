from __future__ import annotations

from pathlib import Path

import pytest

from tools.sdef.parser import load_sdef

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "tools" / "sdef" / "suite.sdef"


def test_load_sdef_parses_repository_suite_fixture() -> None:
    dictionary = load_sdef(FIXTURE_PATH)

    assert dictionary.title == "Dictionary"
    assert len(dictionary.suite) == 2

    save_command = None
    open_command = None

    for suite in dictionary.suite:
        for command in suite.command:
            if command.name == "save":
                save_command = command
            if command.name == "open":
                open_command = command

    assert save_command is not None
    assert open_command is not None
    assert save_command.access_group
    assert save_command.access_group[0].identifier == "*"

    assert open_command.direct_parameter
    assert open_command.direct_parameter[0].type is None
    assert open_command.direct_parameter[0].type_element
    assert open_command.direct_parameter[0].type_element[0].type == "file"
    assert open_command.direct_parameter[0].type_element[0].list == "yes"


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
