from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from typing import Any, ClassVar, Generic, TypeVar

from openmac.apps._internal.filterer import Filterer
from openmac.apps.exceptions import MultipleObjectsReturnedError, ObjectDoesNotExistError

BaseObjectT = TypeVar("BaseObjectT", bound="BaseObject")


@dataclass(slots=True, kw_only=True)
class BaseApplication:
    pass


@dataclass(slots=True, kw_only=True)
class BaseObject:
    pass


@dataclass(slots=True, kw_only=True)
class BaseManager(ABC, Generic[BaseObjectT]):
    _FILTERER_CLASS: ClassVar = Filterer[BaseObjectT]

    _loaded: bool = field(default=False)
    __objects: list[BaseObjectT] = field(default_factory=list)

    def __iter__(self) -> Iterator[BaseObjectT]:
        return iter(self._objects)

    def get(self, **filters: Any) -> BaseObjectT:
        objects = self.filter(**filters)
        if objects.count == 0:
            msg = f"{type(self).__name__}.get() found 0 objects for criteria {filters!r}"
            raise ObjectDoesNotExistError(msg)
        if objects.count > 1:
            msg = f"{type(self).__name__}.get() found {objects.count} objects for criteria {filters!r}, expected 1"
            raise MultipleObjectsReturnedError(msg)

        return objects.first

    def filter(self, **filters: Any) -> BaseManager[BaseObjectT]:
        filterer = self._FILTERER_CLASS(filters)
        filtered_objects = filterer.filter(self._objects)
        return replace(self, __objects=filtered_objects)

    def exclude(self, **filters: Any) -> BaseManager[BaseObjectT]:
        filterer = self._FILTERER_CLASS(filters)
        filtered_objects = filterer.exclude(self._objects)
        return replace(self, __objects=filtered_objects)

    @property
    def all(self) -> list[BaseObjectT]:
        return self._objects

    @property
    def first(self) -> BaseObjectT:
        if not self._objects:
            raise ObjectDoesNotExistError(f"{type(self).__name__} contains no objects.")

        return self._objects[0]

    @property
    def last(self) -> BaseObjectT:
        if not self._objects:
            raise ObjectDoesNotExistError(f"{type(self).__name__} contains no objects.")

        return self._objects[-1]

    @property
    def count(self) -> int:
        return len(self._objects)

    @abstractmethod
    def _load(self) -> list[BaseObjectT]: ...

    @property
    def _objects(self) -> list[BaseObjectT]:
        if not self._loaded:
            objects = self._load()
            self._loaded = True
            self.__objects = objects

        return self.__objects
