from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from openmac.apps.exceptions import MultipleObjectsReturnedError, ObjectDoesNotExistError
from openmac.apps.shared.filterer import Filterer, Q

BaseObjectT = TypeVar("BaseObjectT")


@dataclass(slots=True, kw_only=True)
class BaseApplication:
    pass


@dataclass(slots=True, kw_only=True)
class BaseObject:
    pass


@dataclass(slots=True, kw_only=True)
class BaseManager(ABC, Generic[BaseObjectT]):
    _filterer: Filterer[BaseObjectT] = field(default_factory=Filterer, init=False)

    def __iter__(self) -> Iterator[BaseObjectT]:
        return iter(self.all)

    def get(self, **filters: Any) -> BaseObjectT:
        objects = self.filter(**filters).all
        if len(objects) == 0:
            msg = f"{type(self).__name__}.get() found 0 objects for criteria {filters!r}"
            raise ObjectDoesNotExistError(msg)
        if len(objects) > 1:
            msg = (
                f"{type(self).__name__}.get() found {len(objects)} objects "
                f"for criteria {filters!r}, expected 1"
            )
            raise MultipleObjectsReturnedError(msg)

        return objects[0]

    def filter(self, **filters: Any) -> BaseManager[BaseObjectT]:
        self._filterer.update_query(Q(**filters))
        return self

    def exclude(self, **filters: Any) -> BaseManager[BaseObjectT]:
        self._filterer.update_query(~Q(**filters))
        return self

    @property
    def all(self) -> list[BaseObjectT]:
        return self._filterer.filter(list(self._iter_objects()))

    @property
    def first(self) -> BaseObjectT:
        objects = self.all
        if objects:
            return objects[0]

        raise ObjectDoesNotExistError(f"{type(self).__name__} contains no objects.")

    @property
    def last(self) -> BaseObjectT:
        objects = self.all

        if not objects:
            raise ObjectDoesNotExistError(f"{type(self).__name__} contains no objects.")

        return objects[-1]

    @property
    def count(self) -> int:
        return len(self.all)

    @abstractmethod
    def _iter_objects(self) -> Iterator[BaseObjectT]:
        """Load all available objects without applying query/filter state."""
