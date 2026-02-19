from __future__ import annotations

import dataclasses
import math
import re
from collections.abc import Mapping
from operator import itemgetter
from typing import Final, Protocol, TypeAlias, TypeVar, cast, overload, runtime_checkable

from pydantic import BaseModel, TypeAdapter, ValidationError

from openmac._internal.sdef.types import (
    Date,
    File,
    LocationSpecifier,
    Point,
    Record,
    Rectangle,
    Specifier,
)

RECORD_IDENTIFIER_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
CYCLE_ERROR_MESSAGE = "Cycle detected while serializing AppleScript value."
_NUMBER_PATTERN = re.compile(r"-?(?:[0-9]+\.[0-9]+|[0-9]+)(?:[eE][+-]?[0-9]+)?")
_COLLECTION_DELIMITERS: Final[frozenset[str]] = frozenset({",", "}"})
_UNSET: Final = object()
_NO_MATCH: Final = object()
_T = TypeVar("_T")


@runtime_checkable
class AppleScriptExpression(Protocol):
    def __applescript__(self) -> str: ...


def dumps(value: object) -> str:
    return _serialize(value, seen_container_ids=set())


@overload
def loads(source: str) -> object: ...


@overload
def loads(source: str, *, expected: type[_T]) -> _T: ...


@overload
def loads(source: str, *, expected: object) -> object: ...


def loads(source: object, *, expected: object = _UNSET) -> object:
    if not isinstance(source, str):
        msg = "AppleScript source must be str."
        raise TypeError(msg)

    parser = _ExpressionParser(source=source, allow_raw_expression=expected is not _UNSET)
    parsed = parser.parse()

    if expected is _UNSET:
        return _materialize_untyped(parsed)

    try:
        return TypeAdapter(expected).validate_python(
            _materialize_typed_input(parsed),
            by_alias=True,
            by_name=False,
        )
    except ValidationError as exc:
        msg = "AppleScript value does not match expected type."
        raise TypeError(msg) from exc


def _serialize(value: object, seen_container_ids: set[int]) -> str:
    extension_expression = _serialize_extension_hook(value)
    if extension_expression is not None:
        return extension_expression

    sdef_expression = _serialize_sdef_value(value, seen_container_ids)
    if sdef_expression is not None:
        return sdef_expression

    primitive_expression = _serialize_primitive_value(value)
    if primitive_expression is not None:
        return primitive_expression

    model_expression = _serialize_model_value(value, seen_container_ids)
    if model_expression is not None:
        return model_expression

    container_expression = _serialize_container_value(value, seen_container_ids)
    if container_expression is not None:
        return container_expression

    msg = f"Unsupported value type for AppleScript serialization: {type(value).__name__}."
    raise TypeError(msg)


def _serialize_extension_hook(value: object) -> str | None:
    if not isinstance(value, AppleScriptExpression):
        return None

    expression: object = value.__applescript__()
    if not isinstance(expression, str):
        msg = "__applescript__() must return str."
        raise TypeError(msg)

    return expression


def _serialize_sdef_value(value: object, seen_container_ids: set[int]) -> str | None:
    expression: str | None = None

    if isinstance(value, (Specifier, LocationSpecifier)):
        expression = str(value)
    elif isinstance(value, File):
        expression = f"POSIX file {_serialize_string(str(value))}"
    elif isinstance(value, Date):
        expression = _serialize_string(str(value))
    elif isinstance(value, Point):
        expression = f"{{{value.x}, {value.y}}}"
    elif isinstance(value, Rectangle):
        expression = f"{{{value.left}, {value.top}, {value.right}, {value.bottom}}}"
    elif isinstance(value, Record):
        expression = _serialize_mapping(
            cast("Mapping[object, object]", value.data),
            seen_container_ids,
        )

    return expression


def _serialize_primitive_value(value: object) -> str | None:
    expression: str | None = None

    if value is None:
        expression = "missing value"
    elif isinstance(value, bool):
        expression = "true" if value else "false"
    elif isinstance(value, int):
        expression = str(value)
    elif isinstance(value, float):
        if not math.isfinite(value):
            msg = "AppleScript does not support non-finite float values."
            raise TypeError(msg)
        expression = str(value)
    elif isinstance(value, str):
        expression = _serialize_string(value)

    return expression


def _serialize_model_value(value: object, seen_container_ids: set[int]) -> str | None:
    mapping_value: Mapping[object, object] | None = None

    if isinstance(value, BaseModel):
        mapping_value = cast("Mapping[object, object]", value.model_dump(by_alias=True))
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        mapping_value = cast("Mapping[object, object]", dataclasses.asdict(value))

    if mapping_value is None:
        return None

    return _serialize_mapping(mapping_value, seen_container_ids)


def _serialize_container_value(value: object, seen_container_ids: set[int]) -> str | None:
    expression: str | None = None

    if isinstance(value, Mapping):
        expression = _serialize_mapping(value, seen_container_ids)
    elif isinstance(value, (list, tuple)):
        expression = _serialize_sequence(value, seen_container_ids)
    elif isinstance(value, (set, frozenset)):
        expression = _serialize_set(value, seen_container_ids)

    return expression


def _serialize_string(value: str) -> str:
    if '"' not in value:
        return f'"{value}"'

    return " & quote & ".join(f'"{part}"' for part in value.split('"'))


def _serialize_sequence(
    value: list[object] | tuple[object, ...],
    seen_container_ids: set[int],
) -> str:
    container_id = _track_container(value, seen_container_ids)
    try:
        serialized_values = ", ".join(_serialize(item, seen_container_ids) for item in value)
    finally:
        seen_container_ids.remove(container_id)
    return f"{{{serialized_values}}}"


def _serialize_set(value: set[object] | frozenset[object], seen_container_ids: set[int]) -> str:
    container_id = _track_container(value, seen_container_ids)
    try:
        serialized_values = sorted(_serialize(item, seen_container_ids) for item in value)
    finally:
        seen_container_ids.remove(container_id)
    return f"{{{', '.join(serialized_values)}}}"


def _serialize_mapping(value: Mapping[object, object], seen_container_ids: set[int]) -> str:
    container_id = _track_container(value, seen_container_ids)
    try:
        serialized_items: list[tuple[str, str]] = []
        for key, item in value.items():
            if not isinstance(key, str):
                msg = "AppleScript record keys must be strings."
                raise TypeError(msg)
            label = _serialize_record_key(key)
            serialized_items.append((key, f"{label}:{_serialize(item, seen_container_ids)}"))
        serialized_items.sort(key=itemgetter(0))
        serialized_values = ", ".join(item for _, item in serialized_items)
    finally:
        seen_container_ids.remove(container_id)
    return f"{{{serialized_values}}}"


def _serialize_record_key(key: str) -> str:
    if "|" in key:
        msg = "AppleScript record keys cannot contain '|'."
        raise TypeError(msg)

    if RECORD_IDENTIFIER_PATTERN.fullmatch(key):
        return key

    return f"|{key}|"


def _track_container(value: object, seen_container_ids: set[int]) -> int:
    container_id = id(value)
    if container_id in seen_container_ids:
        raise ValueError(CYCLE_ERROR_MESSAGE)
    seen_container_ids.add(container_id)
    return container_id


@dataclasses.dataclass(frozen=True)
class _PosixFileLiteral:
    path: str


ParsedAppleScriptValue: TypeAlias = (
    bool
    | int
    | float
    | str
    | list["ParsedAppleScriptValue"]
    | dict[str, "ParsedAppleScriptValue"]
    | _PosixFileLiteral
    | None
)


@dataclasses.dataclass(slots=True)
class _ExpressionParser:
    source: str
    allow_raw_expression: bool
    index: int = 0

    def parse(self) -> ParsedAppleScriptValue:
        self._skip_whitespace()
        value = self._parse_value(delimiters=frozenset())
        self._skip_whitespace()
        if not self._is_end():
            raise self._value_error("Unexpected trailing content.")
        return value

    def _parse_value(self, *, delimiters: frozenset[str]) -> ParsedAppleScriptValue:
        self._skip_whitespace()
        if self._is_end():
            raise self._value_error("Unexpected end of input.")

        current_char = self._peek_char()
        if current_char == "{":
            return self._parse_braced_value()
        if current_char == '"':
            return self._parse_string_expression()

        literal_parsers = (
            self._try_parse_posix_file,
            self._try_parse_missing_value,
            self._try_parse_boolean,
            self._try_parse_number,
        )
        parsed_value: object = _NO_MATCH
        for parse_literal in literal_parsers:
            parsed_value = parse_literal(delimiters=delimiters)
            if parsed_value is not _NO_MATCH:
                break
        if parsed_value is not _NO_MATCH:
            return cast("ParsedAppleScriptValue", parsed_value)

        if self.allow_raw_expression:
            return self._parse_raw_expression(delimiters=delimiters)

        if current_char in delimiters:
            raise self._value_error("Expected AppleScript value.")

        msg = "Raw AppleScript expression requires 'expected'."
        raise self._value_error(msg)

    def _parse_braced_value(self) -> ParsedAppleScriptValue:
        self._consume_character("{")
        self._skip_whitespace()

        if self._is_end():
            raise self._value_error("Unexpected end of input.")

        if self._consume_if("}"):
            return []

        if self._looks_like_record():
            return self._parse_record()
        return self._parse_list()

    def _parse_list(self) -> list[ParsedAppleScriptValue]:
        items: list[ParsedAppleScriptValue] = []
        while True:
            items.append(self._parse_value(delimiters=_COLLECTION_DELIMITERS))
            self._skip_whitespace()

            if self._consume_if("}"):
                return items
            if not self._consume_if(","):
                raise self._value_error("Expected ',' or '}' after list item.")

            self._skip_whitespace()
            if self._is_end() or self._peek_char() == "}":
                raise self._value_error("Trailing comma in list.")

    def _parse_record(self) -> dict[str, ParsedAppleScriptValue]:
        items: dict[str, ParsedAppleScriptValue] = {}
        item_index = 0

        while True:
            key = self._parse_record_key(item_index=item_index)
            self._skip_whitespace()
            if not self._consume_if(":"):
                msg = f"Expected ':' after record key at item {item_index}."
                raise self._value_error(msg)

            self._skip_whitespace()
            items[key] = self._parse_value(delimiters=_COLLECTION_DELIMITERS)
            item_index += 1
            self._skip_whitespace()

            if self._consume_if("}"):
                return items
            if not self._consume_if(","):
                raise self._value_error("Expected ',' or '}' after record item.")

            self._skip_whitespace()
            if self._is_end() or self._peek_char() == "}":
                raise self._value_error("Trailing comma in record.")

    def _looks_like_record(self) -> bool:
        current_char = self._peek_char()
        if current_char == "|":
            closing_index = self.source.find("|", self.index + 1)
            if closing_index == -1:
                raise self._value_error("Unterminated pipe label in record key.")
            probe_index = self._skip_whitespace_from(closing_index + 1)
            return probe_index < len(self.source) and self.source[probe_index] == ":"

        if not _is_identifier_start_char(current_char):
            return False

        probe_index = self.index + 1
        while probe_index < len(self.source) and _is_identifier_part_char(self.source[probe_index]):
            probe_index += 1
        probe_index = self._skip_whitespace_from(probe_index)
        return probe_index < len(self.source) and self.source[probe_index] == ":"

    def _parse_record_key(self, *, item_index: int) -> str:
        key_position = self.index
        if self._is_end():
            msg = f"Invalid record key at item {item_index}."
            raise self._value_error(msg, position=key_position)

        current_char = self._peek_char()
        if current_char == "|":
            self.index += 1
            key_start = self.index
            closing_index = self.source.find("|", key_start)
            if closing_index == -1:
                msg = f"Invalid record key at item {item_index}: missing closing '|'."
                raise self._value_error(msg, position=key_position)
            key = self.source[key_start:closing_index]
            self.index = closing_index + 1
            return key

        if not _is_identifier_start_char(current_char):
            msg = f"Invalid record key at item {item_index}: expected identifier or pipe label."
            raise self._value_error(msg, position=key_position)

        start = self.index
        self.index += 1
        while self.index < len(self.source) and _is_identifier_part_char(self.source[self.index]):
            self.index += 1
        return self.source[start : self.index]

    def _parse_string_expression(self) -> str:
        parts = [self._parse_string_literal()]

        while True:
            self._skip_whitespace()
            if not self._consume_if("&"):
                return '"'.join(parts)

            self._skip_whitespace()
            if not self.source.startswith("quote", self.index):
                raise self._value_error("Expected 'quote' in string concatenation.")
            self.index += len("quote")
            self._skip_whitespace()
            if not self._consume_if("&"):
                raise self._value_error("Expected '&' after 'quote' in string concatenation.")
            self._skip_whitespace()
            parts.append(self._parse_string_literal())

    def _parse_string_literal(self) -> str:
        self._consume_character('"')
        literal_start = self.index
        closing_index = self.source.find('"', literal_start)
        if closing_index == -1:
            raise self._value_error("Unterminated string literal.", position=literal_start - 1)

        self.index = closing_index + 1
        return self.source[literal_start:closing_index]

    def _try_parse_missing_value(self, *, delimiters: frozenset[str]) -> object:
        keyword = "missing value"
        if not self.source.startswith(keyword, self.index):
            return _NO_MATCH

        token_end = self.index + len(keyword)
        if not self._is_value_terminated(token_end, delimiters):
            return _NO_MATCH

        self.index = token_end
        return None

    def _try_parse_boolean(self, *, delimiters: frozenset[str]) -> object:
        if self.source.startswith("true", self.index):
            token_end = self.index + len("true")
            if self._is_value_terminated(token_end, delimiters):
                self.index = token_end
                return True

        if self.source.startswith("false", self.index):
            token_end = self.index + len("false")
            if self._is_value_terminated(token_end, delimiters):
                self.index = token_end
                return False

        return _NO_MATCH

    def _try_parse_number(self, *, delimiters: frozenset[str]) -> object:
        match = _NUMBER_PATTERN.match(self.source, self.index)
        if match is None:
            return _NO_MATCH

        token_end = match.end()
        if not self._is_value_terminated(token_end, delimiters):
            return _NO_MATCH

        token = match.group(0)
        self.index = token_end
        if "." in token or "e" in token or "E" in token:
            return float(token)
        return int(token)

    def _try_parse_posix_file(self, *, delimiters: frozenset[str]) -> object:
        keyword = "POSIX file"
        if not self.source.startswith(keyword, self.index):
            return _NO_MATCH

        token_end = self.index + len(keyword)
        if token_end >= len(self.source) or not self.source[token_end].isspace():
            return _NO_MATCH

        self.index = self._skip_whitespace_from(token_end)
        if self._is_end() or self._peek_char() != '"':
            raise self._value_error("Expected string expression after 'POSIX file'.")

        path = self._parse_string_expression()
        if not self._is_value_terminated(self.index, delimiters):
            raise self._value_error("Unexpected content after POSIX file literal.")
        return _PosixFileLiteral(path=path)

    def _parse_raw_expression(self, *, delimiters: frozenset[str]) -> str:
        expression_start = self.index
        while not self._is_end():
            current_char = self._peek_char()
            if current_char in delimiters:
                break
            if current_char == '"':
                self._parse_string_literal()
                continue
            self.index += 1

        expression = self.source[expression_start : self.index].strip()
        if not expression:
            raise self._value_error("Expected AppleScript expression.")
        return expression

    def _is_value_terminated(self, token_end: int, delimiters: frozenset[str]) -> bool:
        probe_index = self._skip_whitespace_from(token_end)
        if probe_index >= len(self.source):
            return True
        return self.source[probe_index] in delimiters

    def _consume_if(self, token: str) -> bool:
        if self.source.startswith(token, self.index):
            self.index += len(token)
            return True
        return False

    def _consume_character(self, token: str) -> None:
        if self._consume_if(token):
            return
        msg = f"Expected {token!r}."
        raise self._value_error(msg)

    def _peek_char(self) -> str:
        return self.source[self.index]

    def _skip_whitespace(self) -> None:
        self.index = self._skip_whitespace_from(self.index)

    def _skip_whitespace_from(self, start: int) -> int:
        index = start
        while index < len(self.source) and self.source[index].isspace():
            index += 1
        return index

    def _is_end(self) -> bool:
        return self.index >= len(self.source)

    def _value_error(self, message: str, *, position: int | None = None) -> ValueError:
        cursor = self.index if position is None else position
        return ValueError(f"{message} (position {cursor}).")


def _materialize_untyped(value: ParsedAppleScriptValue) -> object:
    if isinstance(value, _PosixFileLiteral):
        return File(value.path)
    if isinstance(value, list):
        return [_materialize_untyped(item) for item in value]
    if isinstance(value, dict):
        return {key: _materialize_untyped(item) for key, item in value.items()}
    return value


def _materialize_typed_input(value: ParsedAppleScriptValue) -> object:
    if isinstance(value, _PosixFileLiteral):
        return value.path
    if isinstance(value, list):
        return [_materialize_typed_input(item) for item in value]
    if isinstance(value, dict):
        return {key: _materialize_typed_input(item) for key, item in value.items()}
    return value


def _is_identifier_start_char(char: str) -> bool:
    return char == "_" or "A" <= char <= "Z" or "a" <= char <= "z"


def _is_identifier_part_char(char: str) -> bool:
    return _is_identifier_start_char(char) or "0" <= char <= "9"
