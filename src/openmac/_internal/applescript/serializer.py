from __future__ import annotations

import dataclasses
import math
import re
from collections.abc import Mapping
from operator import itemgetter
from typing import Protocol, cast, runtime_checkable

from pydantic import BaseModel

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


@runtime_checkable
class AppleScriptExpression(Protocol):
    def __applescript__(self) -> str: ...


def dumps(value: object) -> str:
    return _serialize(value, seen_container_ids=set())


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
