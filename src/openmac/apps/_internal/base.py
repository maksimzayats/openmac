from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, ClassVar, Generic, TypeVar

from appscript.reference import GenericReference, app
from openmac.apps.exceptions import ObjectDoesNotExistError, MultipleObjectsReturnedError

BaseObjectT = TypeVar("BaseObjectT", bound="BaseObject")


class BaseApplication:
    _BUNDLE_ID: ClassVar[str]

    def __init__(self) -> None:
        self._ae_object = app(id=self._BUNDLE_ID)


@dataclass(slots=True)
class BaseObject:
    _ae_object: GenericReference


@dataclass(slots=True)
class BaseManager(Generic[BaseObjectT]):
    _objects: list[BaseObjectT]

    def __iter__(self) -> Iterator[BaseObjectT]:
        return iter(self._objects)

    def get(self, **filters: Any) -> BaseObjectT:
        objects = self.filter(**filters)
        if objects.count() == 0:
            msg = f"{type(self).__name__}.get() found 0 objects for criteria {filters!r}"
            raise ObjectDoesNotExistError(msg)
        if objects.count() > 1:
            msg = f"{type(self).__name__}.get() found {objects.count()} objects for criteria {filters!r}, expected 1"
            raise MultipleObjectsReturnedError(msg)

        return objects.first()

    def filter(self, **filters: Any) -> BaseManager[BaseObjectT]:
        pass

    def all(self) -> list[BaseObjectT]:
        return self._objects

    def first(self) -> BaseObjectT | None:
        return self._objects[0] if self._objects else None

    def last(self) -> BaseObjectT | None:
        return self._objects[-1] if self._objects else None

    def count(self) -> int:
        return len(self._objects)
