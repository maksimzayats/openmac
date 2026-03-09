from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Hashable, Iterator
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


@dataclass(slots=True)
class UniqueIterationTracker[TrackedObjectT: Hashable]:
    """Track unique objects discovered across iterations.

    The caller owns any stop condition logic, such as a limit on consecutive
    iterations without new objects.
    """

    _seen_objects: set[TrackedObjectT] = field(default_factory=set, init=False)
    _empty_iterations_in_a_row: int = field(default=0, init=False)
    _has_started: bool = field(default=False, init=False)
    _new_objects_in_current_iteration: int = field(default=0, init=False)

    def new_iteration(self) -> None:
        """Start a new iteration and finalize the previous one."""

        if self._has_started:
            if self._new_objects_in_current_iteration == 0:
                self._empty_iterations_in_a_row += 1
            else:
                self._empty_iterations_in_a_row = 0

        self._has_started = True
        self._new_objects_in_current_iteration = 0

    def add(self, obj: TrackedObjectT) -> bool:
        """Record a discovered object and report whether it is new."""

        if obj in self._seen_objects:
            return False

        self._seen_objects.add(obj)
        self._new_objects_in_current_iteration += 1
        return True

    @property
    def empty_iterations_in_a_row(self) -> int:
        """Return the number of consecutive iterations without new objects."""

        return self._empty_iterations_in_a_row

    def __len__(self) -> int:
        """Return the number of unique objects seen so far."""

        return len(self._seen_objects)


@dataclass(slots=True, kw_only=True)
class BaseManager(ABC, Generic[BaseObjectT_co]):  # noqa: UP046
    _filterer: Filterer[BaseObjectT_co] = field(default_factory=Filterer, init=False)

    def __iter__(self) -> Iterator[BaseObjectT_co]:
        for obj in self._iter_objects():
            if self._filterer.matches_criteria(obj):
                yield obj

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
        for obj in self:
            return obj

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
