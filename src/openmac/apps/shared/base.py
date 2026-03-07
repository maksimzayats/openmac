from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from openmac.apps.exceptions import MultipleObjectsReturnedError, ObjectDoesNotExistError
from openmac.apps.shared.filterer import Filterer, Q

BaseObjectT_co = TypeVar("BaseObjectT_co", covariant=True)


@dataclass(slots=True, kw_only=True)
class BaseApplication:
    pass


@dataclass(slots=True, kw_only=True)
class BaseObject:
    pass


@dataclass(slots=True, kw_only=True)
class BaseManager(ABC, Generic[BaseObjectT_co]):  # noqa: UP046
    _filterer: Filterer[BaseObjectT_co] = field(default_factory=Filterer, init=False)

    def __iter__(self) -> Iterator[BaseObjectT_co]:
        return iter(self.all)

    def get(self, **filters: Any) -> BaseObjectT_co:
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

    def filter(self, **filters: Any) -> BaseManager[BaseObjectT_co]:
        self._filterer.update_query(Q(**filters))
        return self

    def exclude(self, **filters: Any) -> BaseManager[BaseObjectT_co]:
        self._filterer.update_query(~Q(**filters))
        return self

    @property
    def all(self) -> list[BaseObjectT_co]:
        return self._filterer.filter(list(self._iter_objects()))

    @property
    def first(self) -> BaseObjectT_co:
        objects = self.all
        if objects:
            return objects[0]

        raise ObjectDoesNotExistError(f"{type(self).__name__} contains no objects.")

    @property
    def last(self) -> BaseObjectT_co:
        objects = self.all

        if not objects:
            raise ObjectDoesNotExistError(f"{type(self).__name__} contains no objects.")

        return objects[-1]

    @property
    def count(self) -> int:
        return len(self.all)

    @abstractmethod
    def _iter_objects(self) -> Iterator[BaseObjectT_co]:
        """Load all available objects without applying query/filter state."""
