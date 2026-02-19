from __future__ import annotations

from dataclasses import dataclass

import pytest
from pydantic import BaseModel, Field

from openmac._internal.applescript import dumps
from openmac._internal.sdef.types import (
    Date,
    File,
    LocationSpecifier,
    Point,
    Record,
    Rectangle,
    Specifier,
)


class RawExpression:
    def __applescript__(self) -> str:
        return "window 1"


class InvalidExpression:
    def __applescript__(self) -> int:
        return 1


@dataclass
class DemoDataclass:
    foo: int
    given_name: str


class AliasModel(BaseModel):
    given_name: str = Field(alias="given name")


def test_dumps_primitives() -> None:
    true_value = bool(1)
    false_value = bool(0)

    assert dumps(None) == "missing value"
    assert dumps(true_value) == "true"
    assert dumps(false_value) == "false"
    assert dumps(1) == "1"
    assert dumps(1.5) == "1.5"

    with pytest.raises(TypeError, match="non-finite float values"):
        dumps(float("nan"))


def test_dumps_strings() -> None:
    assert dumps("abc") == '"abc"'
    assert dumps('a"b') == '"a" & quote & "b"'
    assert dumps("a\nb") == '"a\nb"'


def test_dumps_lists_tuples_and_sets_with_deterministic_order() -> None:
    assert dumps([1, "a"]) == '{1, "a"}'
    assert dumps(()) == "{}"
    assert dumps({"b", "a"}) == '{"a", "b"}'


def test_dumps_records_and_mapping_keys() -> None:
    assert dumps({"foo": 1}) == "{foo:1}"
    assert dumps({"given name": "x"}) == '{|given name|:"x"}'
    assert dumps({"b": 1, "a": 2}) == "{a:2, b:1}"

    invalid_mapping: dict[object, object] = {1: "x"}
    with pytest.raises(TypeError, match="record keys must be strings"):
        dumps(invalid_mapping)

    with pytest.raises(TypeError, match="cannot contain '\\|'"):
        dumps({"a|b": "x"})


def test_dumps_sdef_types() -> None:
    file_path = f"/{'tmp'}/a"

    assert dumps(Specifier("window 1")) == "window 1"
    assert dumps(LocationSpecifier("location specifier")) == "location specifier"
    assert dumps(File(file_path)) == 'POSIX file "/tmp/a"'
    assert dumps(Date("2026-02-18")) == '"2026-02-18"'
    assert dumps(Record({"foo": 1})) == "{foo:1}"
    assert dumps(Point(1, 2)) == "{1, 2}"
    assert dumps(Rectangle(1, 2, 3, 4)) == "{1, 2, 3, 4}"


def test_dumps_supports_applescript_expression_protocol() -> None:
    assert dumps(RawExpression()) == "window 1"


def test_dumps_rejects_invalid_applescript_expression_return_type() -> None:
    with pytest.raises(TypeError, match="must return str"):
        dumps(InvalidExpression())


def test_dumps_pydantic_model_uses_aliases() -> None:
    value = AliasModel.model_validate({"given name": "x"})

    assert dumps(value) == '{|given name|:"x"}'


def test_dumps_dataclass() -> None:
    value = DemoDataclass(foo=1, given_name="x")

    assert dumps(value) == '{foo:1, given_name:"x"}'


def test_dumps_dataclass_type_is_not_treated_as_dataclass_instance() -> None:
    with pytest.raises(TypeError, match="Unsupported value type"):
        dumps(DemoDataclass)


def test_dumps_rejects_unknown_type() -> None:
    with pytest.raises(TypeError, match="Unsupported value type"):
        dumps(object())


def test_dumps_detects_recursive_list() -> None:
    value: list[object] = []
    value.append(value)

    with pytest.raises(ValueError, match="Cycle detected while serializing AppleScript value"):
        dumps(value)
