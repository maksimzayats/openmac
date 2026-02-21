from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

from appscript import Keyword

from openmac.apps._internal.base import BaseManager, BaseObject

if TYPE_CHECKING:
    from collections.abc import Collection

    from typing_extensions import Unpack


class BookmarkFolders(BaseObject):
    # region Properties

    @property
    def id(self) -> str:
        return self._ae_object.id()

    @property
    def properties(self) -> BookmarkFoldersProperties:
        ae_properties = self._ae_object.properties()
        print(ae_properties)
        return BookmarkFoldersProperties(
            id=ae_properties[Keyword("id")],
            title=ae_properties[Keyword("title")],
            index=ae_properties[Keyword("index")],
        )

    # endregion Properties

    # region Actions

    # endregion Actions


@dataclass(slots=True)
class BookmarkFoldersProperties:
    id: str
    title: str
    index: int


@dataclass(slots=True)
class BookmarkFoldersManager(BaseManager[BookmarkFolders]):
    if TYPE_CHECKING:
        # fmt: off
        def get(self, **filters: Unpack[BookmarkFoldersFilter]) -> BookmarkFolders: ...  # type: ignore[override]
        def filter(self, **filters: Unpack[BookmarkFoldersFilter]) -> BaseManager[BookmarkFolders]: ...  # type: ignore[override]
        def exclude(self, **filters: Unpack[BookmarkFoldersFilter]) -> BaseManager[BookmarkFolders]: ...  # type: ignore[override]
        # fmt: on


class BookmarkFoldersFilter(TypedDict, total=False):
    id: str
    id__eq: str
    id__ne: str
    id__in: Collection[str]
    id__contains: str
    id__startswith: str
    id__endswith: str

    title: str
    title__eq: str
    title__ne: str
    title__in: Collection[str]
    title__contains: str
    title__startswith: str
    title__endswith: str

    index: int
    index__eq: int
    index__ne: int
    index__in: Collection[int]
    index__gt: int
    index__gte: int
    index__lt: int
    index__lte: int
