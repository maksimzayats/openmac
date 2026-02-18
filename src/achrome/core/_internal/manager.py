from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from achrome.core._internal.filterer import GenericFilterer
from achrome.core.exceptions import DoesNotExistError, MultipleObjectsReturnedError

if TYPE_CHECKING:
    from typing_extensions import Self

    from achrome.core._internal.context import Context

T = TypeVar("T")


@dataclass(kw_only=True)
class BaseManager(ABC, Generic[T]):
    _context: Context
    _items: list[T] | None = None
    _default_filters: dict[str, Any] = field(default_factory=dict, init=False)

    @property
    def items(self) -> list[T]:
        if self._items is None:
            self._items = self._load_items()

        return self._items

    def filter(
        self,
        **criteria: Any,
    ) -> Self:
        """Filter windows based on the provided criteria.

        If more than one filter is provided, the `OR` operator is applied between them.
        """
        criteria = {**self._default_filters, **criteria}
        filterer = GenericFilterer[T](dict(criteria))
        filtered_items = filterer.filter(self.items)

        return replace(self, _items=filtered_items)

    def get(self, **criteria: Any) -> T:
        filtered_items = self.filter(**criteria).items
        item_count = len(filtered_items)
        manager_name = type(self).__name__

        if item_count == 1:
            return filtered_items[0]
        if item_count == 0:
            raise DoesNotExistError(
                f"{manager_name}.get() found 0 objects for criteria {criteria!r}",
            )

        raise MultipleObjectsReturnedError(
            f"{manager_name}.get() found {item_count} objects for criteria {criteria!r}, expected 1",
        )

    def first(self) -> T:
        items = self.items
        if not items:
            manager_name = type(self).__name__
            raise DoesNotExistError(f"{manager_name}.first() found 0 objects")

        return items[0]

    def last(self) -> T:
        items = self.items
        if not items:
            manager_name = type(self).__name__
            raise DoesNotExistError(f"{manager_name}.last() found 0 objects")

        return items[-1]

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)

    @abstractmethod
    def _load_items(self) -> list[T]:
        """Load items from the Chrome API."""
