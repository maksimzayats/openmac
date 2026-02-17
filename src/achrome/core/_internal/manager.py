from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from achrome.core._internal.filterer import GenericFilterer

if TYPE_CHECKING:
    from typing_extensions import Self

    from achrome.core._internal.context import Context

T = TypeVar("T")


@dataclass(kw_only=True)
class BaseManager(ABC, Generic[T]):
    _context: Context
    _items: list[T] | None = None

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
        filterer = GenericFilterer[T](dict(criteria))
        filtered_items = filterer.filter(self.items)

        return replace(self, _items=filtered_items)

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)

    @abstractmethod
    def _load_items(self) -> list[T]:
        """Load items from the Chrome API."""
