from __future__ import annotations

import operator
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class GenericFilterer(Generic[T]):
    def __init__(self, criteria: dict[str, Any]) -> None:
        self._criteria = criteria

    def filter(self, items: list[T]) -> list[T]:
        return [item for item in items if self._matches_criteria(item)]

    def _matches_criteria(self, item: T) -> bool:
        for key, value in self._criteria.items():
            if "__" in key:
                field_name, operator_name = key.split("__", 1)
            else:
                field_name, operator_name = key, "eq"

            item_value = getattr(item, field_name, None)
            operator_value = getattr(operator, operator_name, None)

            if operator_value is None:
                raise ValueError(f"Unsupported operator: {operator_name}")

            if not operator_value(item_value, value):
                return False

        return True
