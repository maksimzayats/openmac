from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

from appscript import Keyword

from openmac.apps._internal.base import BaseManager, BaseObject

if TYPE_CHECKING:
    from collections.abc import Collection

    from typing_extensions import Unpack


class Tab(BaseObject):
    @property
    def url(self) -> str:
        return self._ae_object.URL()

    @property
    def title(self) -> str:
        return self._ae_object.title()

    @property
    def loading(self) -> bool:
        return self._ae_object.loading()

    @property
    def id(self) -> str:
        return self._ae_object.id()

    @property
    def properties(self) -> TabProperties:
        ae_properties = self._ae_object.properties()
        return TabProperties(
            url=ae_properties[Keyword("URL")],
            title=ae_properties[Keyword("title")],
            loading=ae_properties[Keyword("loading")],
            id=ae_properties[Keyword("id")],
        )


@dataclass(slots=True)
class TabProperties:
    url: str
    title: str
    loading: bool
    id: str


class TabsManager(BaseManager[Tab]):
    if TYPE_CHECKING:

        def get(self, **filters: Unpack[TabsFilter]) -> Tab: ...  # type: ignore[override]
        def filter(self, **filters: Unpack[TabsFilter]) -> BaseManager[Tab]: ...  # type: ignore[override]
        def exclude(self, **filters: Unpack[TabsFilter]) -> BaseManager[Tab]: ...  # type: ignore[override]


class TabsFilter(TypedDict, total=False):
    url: str
    url__eq: str
    url__ne: str
    url__lt: str
    url__lte: str
    url__gt: str
    url__gte: str
    url__in: Collection[str]
    url__contains: str
    url__startswith: str
    url__endswith: str

    title: str
    title__eq: str
    title__ne: str
    title__lt: str
    title__lte: str
    title__gt: str
    title__gte: str
    title__in: Collection[str]
    title__contains: str
    title__startswith: str
    title__endswith: str

    loading: bool
    loading__eq: bool
    loading__ne: bool
    loading__lt: bool
    loading__lte: bool
    loading__gt: bool
    loading__gte: bool
    loading__in: Collection[bool]

    id: str
    id__eq: str
    id__ne: str
    id__lt: str
    id__lte: str
    id__gt: str
    id__gte: str
    id__in: Collection[str]
    id__contains: str
    id__startswith: str
    id__endswith: str
