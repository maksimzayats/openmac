import operator
from typing import TypeVar, Generic, Any, ClassVar

T = TypeVar("T")


class Filterer(Generic[T]):
    _OPERATIONS: ClassVar = {
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
            if "__" in key:
                field_name, operator_name = key.split("__", 1)
            else:
                field_name, operator_name = key, "eq"

            item_value = getattr(item, field_name, None)
            operation = self._OPERATIONS.get(operator_name)

            if operation is None:
                raise ValueError(f"Unsupported operator: {operator_name}")

            if not operation(item_value, value):
                return False

        return True
