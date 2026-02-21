from __future__ import annotations

import operator
from collections.abc import Callable, Iterable
from typing import Any, ClassVar, Final, Generic, TypeVar

from openmac.apps.exceptions import InvalidFilterError

T = TypeVar("T")
FilterOperation = Callable[[Any, Any], bool]
MISSING: Final = object()


class Filterer(Generic[T]):
    _OPERATIONS: ClassVar[dict[str, FilterOperation]] = {
        "": operator.eq,
        "eq": operator.eq,
        "ne": operator.ne,
        "lt": operator.lt,
        "lte": operator.le,
        "gt": operator.gt,
        "gte": operator.ge,
        "in": lambda a, b: a in b,
        "contains": operator.contains,
        "startswith": lambda a, b: str(a).startswith(str(b)),
        "endswith": lambda a, b: str(a).endswith(str(b)),
    }

    def __init__(self, filters: dict[str, Any]) -> None:
        self._filters = filters

    def filter(self, items: list[T]) -> list[T]:
        return [item for item in items if self._matches_criteria(item)]

    def exclude(self, items: list[T]) -> list[T]:
        return [item for item in items if not self._matches_criteria(item)]

    def _matches_criteria(self, item: T) -> bool:
        for key, value in self._filters.items():
            field_path, operator_name = self._parse_lookup(key)
            operation = self._OPERATIONS.get(operator_name)

            if operation is None:
                raise InvalidFilterError(f"Unsupported operator: {operator_name}")

            item_values = self._resolve_field_path(item, field_path, key)
            if not any(operation(item_value, value) for item_value in item_values):
                return False

        return True

    def _parse_lookup(self, key: str) -> tuple[list[str], str]:
        if "__" not in key:
            return [key], "eq"

        field_path, operator_name = key.rsplit("__", 1)
        if operator_name in self._OPERATIONS:
            return field_path.split("__"), operator_name

        return key.split("__"), "eq"

    def _resolve_field_path(self, item: T, field_path: list[str], lookup_key: str) -> list[Any]:
        values: list[Any] = [item]

        for field_name in field_path:
            next_values: list[Any] = []
            for value in values:
                next_values.extend(self._resolve_value(value, field_name, lookup_key))
            values = next_values

            if not values:
                break

        return values

    def _resolve_value(self, value: Any, field_name: str, lookup_key: str) -> list[Any]:
        if value is None:
            return []

        resolved_value = self._get_attribute_value_or_missing(value, field_name)
        if resolved_value is not MISSING and not callable(resolved_value):
            return [resolved_value]

        if self._is_iterable_relation(value):
            return [
                self._get_attribute_value(nested_value, field_name, lookup_key)
                for nested_value in value
                if nested_value is not None
            ]

        msg = f"Invalid filter field '{field_name}' in lookup '{lookup_key}'"
        raise InvalidFilterError(msg)

    def _get_attribute_value(self, value: Any, field_name: str, lookup_key: str) -> Any:
        resolved_value = self._get_attribute_value_or_missing(value, field_name)
        if resolved_value is MISSING:
            msg = f"Invalid filter field '{field_name}' in lookup '{lookup_key}'"
            raise InvalidFilterError(msg)

        return resolved_value

    @staticmethod
    def _get_attribute_value_or_missing(value: Any, field_name: str) -> Any:
        return getattr(value, field_name, MISSING)

    @staticmethod
    def _is_iterable_relation(value: Any) -> bool:
        return isinstance(value, Iterable) and not isinstance(value, str | bytes | bytearray | dict)
