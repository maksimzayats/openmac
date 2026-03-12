from __future__ import annotations

import logging
import operator
from collections.abc import Callable, Hashable, Iterable, Iterator, Mapping
from functools import reduce
from typing import Any, ClassVar, Final, Generic, TypeVar

from openmac.apps.exceptions import InvalidFilterError

T = TypeVar("T")
FilterOperation = Callable[[Any, Any], bool]
MISSING: Final = object()
logger = logging.getLogger(__name__)


class Filterer(Generic[T]):  # noqa: UP046
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

    def __init__(self, query: Q | Mapping[str, Any] | None = None) -> None:
        normalized_query = self._normalize_query(query)
        self._initial_query = normalized_query
        self._query = normalized_query.copy()
        logger.debug("Initialized %s with query=%r", type(self).__name__, self._query)

    @property
    def query(self) -> Q:
        return self._query

    def update_filters(self, **filters: Any) -> None:
        logger.debug("Updating filters with kwargs=%r", filters)
        self.update_query(Q(**filters))

    def update_query(self, query: Q) -> None:
        logger.debug("Combining existing query=%r with query=%r", self._query, query)
        self._query &= query

    def filter(self, items: list[T]) -> list[T]:
        logger.debug("Filtering %s items with query=%r", len(items), self._query)
        return [item for item in items if self.matches_criteria(item)]

    def exclude(self, items: list[T]) -> list[T]:
        logger.debug(
            "Excluding items from %s-item collection with query=%r",
            len(items),
            self._query,
        )
        return [item for item in items if not self.matches_criteria(item)]

    def matches_criteria(self, item: T) -> bool:
        result = self._matches_query(item, self._query)
        logger.debug("Evaluated item=%r against query=%r result=%s", item, self._query, result)
        return result

    def _matches_query(self, item: T, query: Q) -> bool:
        if not query.children:
            result = True
        else:
            child_results = [self._matches_child(item, child) for child in query.children]
            if query.connector == Q.AND:
                result = all(child_results)
            elif query.connector == Q.OR:
                result = any(child_results)
            elif query.connector == Q.XOR:
                result = reduce(operator.xor, child_results)
            else:
                msg = f"Unsupported Q connector: {query.connector}"
                logger.warning(msg)
                raise InvalidFilterError(msg)

        return not result if query.negated else result

    def _matches_child(self, item: T, child: Q | tuple[str, Any]) -> bool:
        if isinstance(child, Q):
            return self._matches_query(item, child)

        key, value = child
        return self._matches_lookup(item, key, value)

    def _matches_lookup(self, item: T, key: str, value: Any) -> bool:
        field_path, operator_name = self._parse_lookup(key)
        operation = self._OPERATIONS.get(operator_name)

        if operation is None:
            logger.warning("Unsupported filter operator=%s in key=%s", operator_name, key)
            raise InvalidFilterError(f"Unsupported operator: {operator_name}")

        item_values = self._resolve_field_path(item, field_path, key)
        return any(operation(item_value, value) for item_value in item_values)

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
        logger.warning(msg)
        raise InvalidFilterError(msg)

    def _get_attribute_value(self, value: Any, field_name: str, lookup_key: str) -> Any:
        resolved_value = self._get_attribute_value_or_missing(value, field_name)
        if resolved_value is MISSING:
            msg = f"Invalid filter field '{field_name}' in lookup '{lookup_key}'"
            logger.warning(msg)
            raise InvalidFilterError(msg)

        return resolved_value

    @staticmethod
    def _get_attribute_value_or_missing(value: Any, field_name: str) -> Any:
        return getattr(value, field_name, MISSING)

    @staticmethod
    def _is_iterable_relation(value: Any) -> bool:
        return isinstance(value, Iterable) and not isinstance(value, str | bytes | bytearray | dict)

    @staticmethod
    def _normalize_query(query: Q | Mapping[str, Any] | None) -> Q:
        if query is None:
            return Q()
        if isinstance(query, Q):
            return query.copy()

        return Q(**dict(query))


class Q:
    AND: ClassVar[str] = "AND"
    OR: ClassVar[str] = "OR"
    XOR: ClassVar[str] = "XOR"
    default: ClassVar[str] = AND
    conditional: ClassVar[bool] = True
    _VALID_CONNECTORS: ClassVar[frozenset[str]] = frozenset({AND, OR, XOR})

    def __init__(
        self,
        *args: Q | tuple[str, Any],
        _connector: str | None = None,
        _negated: bool = False,
        **kwargs: Any,
    ) -> None:
        self.children: list[Q | tuple[str, Any]] = [*args, *sorted(kwargs.items())]
        self.connector = self._validate_connector(_connector)
        self.negated = _negated

    def __bool__(self) -> bool:
        return bool(self.children)

    def __len__(self) -> int:
        return len(self.children)

    def __iter__(self) -> Iterator[Q | tuple[str, Any]]:
        return iter(self.children)

    def __or__(self, other: object) -> Q:
        if not isinstance(other, Q):
            return NotImplemented

        return self._combine(other, self.OR)

    def __and__(self, other: object) -> Q:
        if not isinstance(other, Q):
            return NotImplemented

        return self._combine(other, self.AND)

    def __xor__(self, other: object) -> Q:
        if not isinstance(other, Q):
            return NotImplemented

        return self._combine(other, self.XOR)

    def __invert__(self) -> Q:
        obj = self.copy()
        obj.negate()
        return obj

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Q):
            return NotImplemented

        return self.identity == other.identity

    def __hash__(self) -> int:
        return hash(self.identity)

    def __repr__(self) -> str:
        parts = [repr(child) for child in self.children]
        if self.connector != self.default:
            parts.append(f"_connector={self.connector!r}")
        if self.negated:
            parts.append("_negated=True")

        return f"{type(self).__name__}({', '.join(parts)})"

    @property
    def identity(self) -> tuple[object, ...]:
        path, args, kwargs = self.deconstruct()
        identity: list[object] = [path, *kwargs.items()]

        for child in args:
            if isinstance(child, tuple):
                lookup, value = child
                identity.append((lookup, self._make_hashable(value)))
            else:
                identity.append(child)

        return tuple(identity)

    @property
    def referenced_base_fields(self) -> set[str]:
        fields: set[str] = set()

        for child in self.children:
            if isinstance(child, tuple):
                lookup, _ = child
                fields.add(lookup.split("__", 1)[0])
            else:
                fields.update(child.referenced_base_fields)

        return fields

    @classmethod
    def create(cls, *, connector: str | None = None, negated: bool = False) -> Q:
        return cls(_connector=connector, _negated=negated)

    @classmethod
    def _validate_connector(cls, connector: str | None) -> str:
        resolved_connector = cls.default if connector is None else connector
        if resolved_connector not in cls._VALID_CONNECTORS:
            msg = f"Unsupported Q connector: {resolved_connector}"
            raise ValueError(msg)

        return resolved_connector

    def _combine(self, other: Q, connector: str) -> Q:
        if getattr(other, "conditional", False) is False:
            raise TypeError(other)
        if not self:
            return other.copy()
        if not other:
            return self.copy()

        obj = self.create(connector=connector)
        obj.add(self, connector)
        obj.add(other, connector)
        return obj

    def add(self, child: Q | tuple[str, Any], connector: str) -> None:
        resolved_connector = self._validate_connector(connector)
        if self.children and self.connector != resolved_connector:
            existing = self.copy()
            self.connector = resolved_connector
            self.children = [existing, self._copy_child(child)]
            return

        self.connector = resolved_connector
        if (
            isinstance(child, Q)
            and not child.negated
            and (child.connector == resolved_connector or len(child) == 1)
        ):
            self.children.extend(child.copy().children)
            return

        self.children.append(self._copy_child(child))

    def negate(self) -> None:
        self.negated = not self.negated

    def copy(self) -> Q:
        return type(self)(
            *(self._copy_child(child) for child in self.children),
            _connector=self.connector,
            _negated=self.negated,
        )

    def flatten(self) -> Iterator[object]:
        yield self
        for child in self.children:
            value = child[1] if isinstance(child, tuple) else child
            if isinstance(value, Q):
                yield from value.flatten()
            else:
                yield value

    def deconstruct(self) -> tuple[str, tuple[Q | tuple[str, Any], ...], dict[str, object]]:
        path = f"{type(self).__module__}.{type(self).__name__}"
        args = tuple(self.children)
        kwargs: dict[str, object] = {}
        if self.connector != self.default:
            kwargs["_connector"] = self.connector
        if self.negated:
            kwargs["_negated"] = True

        return path, args, kwargs

    @classmethod
    def _copy_child(cls, child: Q | tuple[str, Any]) -> Q | tuple[str, Any]:
        if isinstance(child, Q):
            return child.copy()

        return child

    @classmethod
    def _make_hashable(cls, value: Any) -> Hashable:
        if isinstance(value, Mapping):
            return tuple(sorted((key, cls._make_hashable(item)) for key, item in value.items()))
        if isinstance(value, list | tuple):
            return tuple(cls._make_hashable(item) for item in value)
        if isinstance(value, set | frozenset):
            return frozenset(cls._make_hashable(item) for item in value)
        if isinstance(value, Hashable):
            return value

        msg = f"Unhashable Q value: {value!r}"
        raise TypeError(msg)
