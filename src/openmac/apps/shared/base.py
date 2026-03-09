from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Hashable, Iterator
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from openmac.apps.exceptions import MultipleObjectsReturnedError, ObjectDoesNotExistError
from openmac.apps.shared.filterer import Filterer, Q

BaseObjectT_co = TypeVar("BaseObjectT_co", covariant=True)
logger = logging.getLogger(__name__)


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
                logger.debug(
                    "Unique iteration finished without new objects; empty_iterations_in_a_row=%s",
                    self._empty_iterations_in_a_row,
                )
            else:
                logger.debug(
                    "Unique iteration finished with %s new objects; resetting empty iteration counter",
                    self._new_objects_in_current_iteration,
                )
                self._empty_iterations_in_a_row = 0

        self._has_started = True
        self._new_objects_in_current_iteration = 0
        logger.debug("Started new unique iteration tracker cycle")

    def add(self, obj: TrackedObjectT) -> bool:
        """Record a discovered object and report whether it is new."""

        if obj in self._seen_objects:
            logger.debug("Unique iteration tracker skipped already seen object: %r", obj)
            return False

        self._seen_objects.add(obj)
        self._new_objects_in_current_iteration += 1
        logger.debug(
            "Unique iteration tracker recorded new object: %r (total_seen=%s current_iteration_new=%s)",
            obj,
            len(self._seen_objects),
            self._new_objects_in_current_iteration,
        )
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
        logger.debug(
            "Iterating %s with query=%r",
            type(self).__name__,
            self._filterer.query,
        )
        for obj in self._iter_objects():
            if self._filterer.matches_criteria(obj):
                logger.debug("%s yielded matching object: %r", type(self).__name__, obj)
                yield obj
                continue

            logger.debug("%s skipped non-matching object: %r", type(self).__name__, obj)

    def get(self, **filters: Any) -> BaseObjectT_co:
        logger.debug("%s.get called with filters=%r", type(self).__name__, filters)
        objects = self.filter(**filters).all
        if len(objects) == 0:
            msg = f"{type(self).__name__}.get() found 0 objects for criteria {filters!r}"
            logger.warning(msg)
            raise ObjectDoesNotExistError(msg)
        if len(objects) > 1:
            msg = (
                f"{type(self).__name__}.get() found {len(objects)} objects "
                f"for criteria {filters!r}, expected 1"
            )
            logger.warning(msg)
            raise MultipleObjectsReturnedError(msg)

        logger.debug("%s.get returning object: %r", type(self).__name__, objects[0])
        return objects[0]

    def filter(self, **filters: Any) -> BaseManager[BaseObjectT_co]:
        logger.debug("%s.filter updating query with filters=%r", type(self).__name__, filters)
        self._filterer.update_query(Q(**filters))
        return self

    def exclude(self, **filters: Any) -> BaseManager[BaseObjectT_co]:
        logger.debug("%s.exclude updating query with filters=%r", type(self).__name__, filters)
        self._filterer.update_query(~Q(**filters))
        return self

    @property
    def all(self) -> list[BaseObjectT_co]:
        logger.debug("%s.all collecting all matching objects", type(self).__name__)
        objects = self._filterer.filter(list(self._iter_objects()))
        logger.debug("%s.all collected %s matching objects", type(self).__name__, len(objects))
        return objects

    @property
    def first(self) -> BaseObjectT_co:
        logger.debug("%s.first requested", type(self).__name__)
        for obj in self:
            logger.debug("%s.first returning object: %r", type(self).__name__, obj)
            return obj

        msg = f"{type(self).__name__} contains no objects."
        logger.warning(msg)
        raise ObjectDoesNotExistError(msg)

    @property
    def last(self) -> BaseObjectT_co:
        logger.debug("%s.last requested", type(self).__name__)
        objects = self.all

        if not objects:
            msg = f"{type(self).__name__} contains no objects."
            logger.warning(msg)
            raise ObjectDoesNotExistError(msg)

        logger.debug("%s.last returning object: %r", type(self).__name__, objects[-1])
        return objects[-1]

    @property
    def count(self) -> int:
        logger.debug("%s.count requested", type(self).__name__)
        count = len(self.all)
        logger.debug("%s.count returning %s", type(self).__name__, count)
        return count

    @abstractmethod
    def _iter_objects(self) -> Iterator[BaseObjectT_co]:
        """Load all available objects without applying query/filter state."""
