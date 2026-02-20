from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar, cast

import pytest
from pydantic import BaseModel, Field, ValidationError

import openmac._internal.applescript.serializer as applescript_serializer
from openmac._internal.applescript import dumps, loads
from openmac._internal.sdef.base import SDEFClass
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


class WindowPayload(BaseModel):
    target: Specifier[SDEFClass] = Field(alias="target object")
    frame: Rectangle


_PayloadT = TypeVar("_PayloadT")


class GenericPayload(BaseModel, Generic[_PayloadT]):
    items: list[_PayloadT]


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


def test_dumps_pydantic_model_generics() -> None:
    first = AliasModel.model_validate({"given name": "a"})
    second = AliasModel.model_validate({"given name": "b"})
    payload = GenericPayload[AliasModel](items=[first, second])

    assert dumps([first, second]) == '{{|given name|:"a"}, {|given name|:"b"}}'
    assert dumps({"b": second, "a": first}) == '{a:{|given name|:"a"}, b:{|given name|:"b"}}'
    assert dumps(payload) == '{items:{{|given name|:"a"}, {|given name|:"b"}}}'


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


def test_loads_primitives() -> None:
    assert loads("missing value") is None
    assert loads("true") is True
    assert loads("false") is False
    assert loads("7") == 7
    assert loads("-3") == -3
    assert loads("1.5") == pytest.approx(1.5)
    assert loads("1e-6") == pytest.approx(1e-6)


def test_loads_strings() -> None:
    assert loads('"abc"') == "abc"
    assert loads('"a\nb\tc"') == "a\nb\tc"
    assert loads('"a" & quote & "b"') == 'a"b'
    assert loads('"a" & quote & "" & quote & "b"') == 'a""b'


def test_loads_collections() -> None:
    assert loads('{1, "a", false}') == [1, "a", False]
    assert loads("{}") == []

    record = loads('{foo:1, |given name|:"x"}')
    assert record == {"foo": 1, "given name": "x"}
    assert isinstance(record, dict)
    assert list(record) == ["foo", "given name"]


def test_loads_posix_file_literal() -> None:
    file_path = f"/{'tmp'}/a"

    assert loads(f'POSIX file "{file_path}"') == File(file_path)
    assert loads(f'{{POSIX file "{file_path}"}}') == [File(file_path)]


def test_loads_is_conservative_without_expected() -> None:
    assert loads('"2026-02-18"') == "2026-02-18"
    assert loads("{1, 2}") == [1, 2]
    assert loads("{left:1, top:2, right:3, bottom:4}") == {
        "left": 1,
        "top": 2,
        "right": 3,
        "bottom": 4,
    }


def test_loads_typed_decode_non_model_values() -> None:
    file_path = f"/{'tmp'}/a"

    assert loads('"2026-02-18"', expected=Date) == Date("2026-02-18")
    assert loads(f'POSIX file "{file_path}"', expected=File) == File(file_path)
    assert loads("{1, 2}", expected=Point) == Point(1, 2)
    assert loads("{1, 2, 3, 4}", expected=Rectangle) == Rectangle(1, 2, 3, 4)
    assert loads("{foo:1}", expected=Record) == Record({"foo": 1})
    assert loads("{{1, 2}, {3, 4}}", expected=list[Point]) == [Point(1, 2), Point(3, 4)]
    assert loads('{"a", "b"}', expected=set[str]) == {"a", "b"}
    assert loads(
        "{first:{1, 2, 3, 4}, second:{5, 6, 7, 8}}",
        expected=dict[str, Rectangle],
    ) == {
        "first": Rectangle(1, 2, 3, 4),
        "second": Rectangle(5, 6, 7, 8),
    }


def test_loads_typed_decode_basemodel_alias_and_nested_usage() -> None:
    alias_model = loads('{|given name|:"x"}', expected=AliasModel)
    assert isinstance(alias_model, AliasModel)
    assert alias_model.given_name == "x"

    payload = loads(
        "{|target object|:window 1, frame:{1, 2, 3, 4}}",
        expected=WindowPayload,
    )
    assert isinstance(payload, WindowPayload)
    assert payload.target == Specifier("window 1")
    assert payload.frame == Rectangle(1, 2, 3, 4)

    payload_list = loads(
        '{{|given name|:"a"}, {|given name|:"b"}}',
        expected=list[AliasModel],
    )
    assert [item.given_name for item in payload_list] == ["a", "b"]


def test_loads_alias_policy_rejects_field_names_when_alias_is_required() -> None:
    with pytest.raises(TypeError, match="does not match expected type"):
        loads('{given_name:"x"}', expected=AliasModel)


def test_loads_raw_expression_policy() -> None:
    with pytest.raises(ValueError, match=r"requires 'expected'.*position"):
        loads("window 1")

    assert loads("window 1", expected=Specifier) == Specifier("window 1")
    assert loads("location specifier", expected=LocationSpecifier) == LocationSpecifier(
        "location specifier",
    )
    assert loads("{target:window 1}", expected=Record) == Record({"target": "window 1"})


def test_loads_invalid_sources_raise_value_error_with_position() -> None:
    bad_sources = ['"abc', "{foo 1}", "{|foo:1}", "{1,}", "true false"]

    for bad_source in bad_sources:
        with pytest.raises(ValueError, match="position"):
            loads(bad_source)


def test_loads_covers_additional_parser_failure_paths() -> None:
    with pytest.raises(ValueError, match="trailing content"):
        loads('"a" "b"')
    with pytest.raises(ValueError, match="Unexpected end of input"):
        loads("{foo:")
    with pytest.raises(ValueError, match="Unexpected end of input"):
        loads("{")
    with pytest.raises(ValueError, match="Expected AppleScript value"):
        loads("{foo:}")
    with pytest.raises(ValueError, match="after list item"):
        loads('{"a" b}')
    with pytest.raises(ValueError, match="after record key at item 1"):
        loads("{foo:1, bar 2}")
    with pytest.raises(ValueError, match="after record item"):
        loads('{foo:"1" bar:2}')
    with pytest.raises(ValueError, match="Trailing comma in record"):
        loads("{foo:1,}")
    with pytest.raises(ValueError, match="missing closing '\\|'"):
        loads("{foo:1, |bar:2}")
    with pytest.raises(ValueError, match="expected identifier or pipe label"):
        loads("{foo:1, 1:2}")
    with pytest.raises(ValueError, match="Expected 'quote' in string concatenation"):
        loads('"a" & nope & "b"')
    with pytest.raises(ValueError, match="Expected '&' after 'quote'"):
        loads('"a" & quote "b"')
    with pytest.raises(ValueError, match="Expected '\"'"):
        loads('"a" & quote & true')
    with pytest.raises(ValueError, match="Expected string expression after 'POSIX file'"):
        loads("POSIX file true")
    with pytest.raises(ValueError, match="Unexpected content after POSIX file literal"):
        loads('POSIX file "a" "b"')
    with pytest.raises(ValueError, match="Expected AppleScript expression"):
        loads("{foo:}", expected=Record)


def test_loads_raw_expression_fallback_when_literals_are_not_terminated() -> None:
    assert loads("missing value and more", expected=Specifier) == Specifier(
        "missing value and more",
    )
    assert loads("false condition", expected=Specifier) == Specifier("false condition")
    assert loads("12abc", expected=Specifier) == Specifier("12abc")
    assert loads("POSIX filesystem", expected=Specifier) == Specifier("POSIX filesystem")
    assert loads('window "Main"', expected=Specifier) == Specifier('window "Main"')


def test_parser_record_key_end_guard() -> None:
    parser = applescript_serializer._ExpressionParser(source="", allow_raw_expression=False)

    with pytest.raises(ValueError, match="Invalid record key at item 0"):
        parser._parse_record_key(item_index=0)


def test_loads_rejects_non_string_source() -> None:
    with pytest.raises(TypeError, match="source must be str"):
        loads(cast("str", 1))


def test_loads_expected_validation_failure_raises_type_error_with_cause() -> None:
    with pytest.raises(TypeError, match="does not match expected type") as exc_info:
        loads('"x"', expected=int)

    assert isinstance(exc_info.value.__cause__, ValidationError)


def test_loads_round_trip_subset_with_expected() -> None:
    alias_model = AliasModel.model_validate({"given name": "x"})
    file_path = f"/{'tmp'}/a"
    cases: list[tuple[object, object]] = [
        (Date("2026-02-18"), Date),
        (File(file_path), File),
        (Point(1, 2), Point),
        (Rectangle(1, 2, 3, 4), Rectangle),
        (Record({"foo": 1}), Record),
        (alias_model, AliasModel),
        ([Point(1, 2), Point(3, 4)], list[Point]),
        ({"frame": Rectangle(1, 2, 3, 4)}, dict[str, Rectangle]),
    ]

    for value, expected in cases:
        expression = dumps(value)
        decoded = loads(expression, expected=expected)
        assert decoded == value
