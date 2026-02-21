from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

from appscript import Keyword

from openmac.apps._internal.base import BaseManager, BaseObject
from openmac.apps.chrome.objects.tab import Tab, TabsManager

if TYPE_CHECKING:
    from collections.abc import Collection

    from typing_extensions import Unpack


class Window(BaseObject):
    @property
    def id(self) -> str:
        return self._ae_object.id()

    @property
    def closeable(self) -> bool:
        return self._ae_object.closeable()

    @property
    def zoomed(self) -> bool:
        return self._ae_object.zoomed()

    @property
    def active_tab_index(self) -> int:
        return self._ae_object.active_tab_index()

    @property
    def index(self) -> int:
        return self._ae_object.index()

    @property
    def visible(self) -> bool:
        return self._ae_object.visible()

    @property
    def given_name(self) -> str:
        return self._ae_object.given_name()

    @property
    def title(self) -> str:
        return self._ae_object.title()

    @property
    def minimizable(self) -> bool:
        return self._ae_object.minimizable()

    @property
    def mode(self) -> str:
        return self._ae_object.mode()

    @property
    def active_tab(self) -> int:
        return self._ae_object.active_tab()

    @property
    def properties(self) -> WindowProperties:
        ae_properties = self._ae_object.properties()
        return WindowProperties(
            id=ae_properties[Keyword("id")],
            closeable=ae_properties[Keyword("closeable")],
            zoomed=ae_properties[Keyword("zoomed")],
            active_tab_index=ae_properties[Keyword("active_tab_index")],
            index=ae_properties[Keyword("index")],
            visible=ae_properties[Keyword("visible")],
            given_name=ae_properties[Keyword("given_name")],
            title=ae_properties[Keyword("title")],
            minimizable=ae_properties[Keyword("minimizable")],
            mode=ae_properties[Keyword("mode")],
            active_tab=ae_properties[Keyword("active_tab")],
        )

    @property
    def tabs(self) -> TabsManager:
        return TabsManager(
            _ae_objects=self._ae_object.tabs,
            _objects=[Tab(_ae_object=ae_tab) for ae_tab in self._ae_object.tabs()],
        )


@dataclass(slots=True)
class WindowProperties:
    id: str
    closeable: bool
    zoomed: bool
    active_tab_index: int
    index: int
    visible: bool
    given_name: str
    title: str
    minimizable: bool
    mode: str
    active_tab: int


class WindowsManager(BaseManager[Window]):
    if TYPE_CHECKING:

        def get(self, **filters: Unpack[WindowsFilter]) -> Window: ...  # type: ignore[override]
        def filter(self, **filters: Unpack[WindowsFilter]) -> BaseManager[Window]: ...  # type: ignore[override]
        def exclude(self, **filters: Unpack[WindowsFilter]) -> BaseManager[Window]: ...  # type: ignore[override]


class WindowsFilter(TypedDict, total=False):
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

    closeable: bool
    closeable__eq: bool
    closeable__ne: bool
    closeable__lt: bool
    closeable__lte: bool
    closeable__gt: bool
    closeable__gte: bool
    closeable__in: Collection[bool]

    zoomed: bool
    zoomed__eq: bool
    zoomed__ne: bool
    zoomed__lt: bool
    zoomed__lte: bool
    zoomed__gt: bool
    zoomed__gte: bool
    zoomed__in: Collection[bool]

    active_tab_index: int
    active_tab_index__eq: int
    active_tab_index__ne: int
    active_tab_index__lt: int
    active_tab_index__lte: int
    active_tab_index__gt: int
    active_tab_index__gte: int
    active_tab_index__in: Collection[int]

    index: int
    index__eq: int
    index__ne: int
    index__lt: int
    index__lte: int
    index__gt: int
    index__gte: int
    index__in: Collection[int]

    visible: bool
    visible__eq: bool
    visible__ne: bool
    visible__lt: bool
    visible__lte: bool
    visible__gt: bool
    visible__gte: bool
    visible__in: Collection[bool]

    given_name: str
    given_name__eq: str
    given_name__ne: str
    given_name__lt: str
    given_name__lte: str
    given_name__gt: str
    given_name__gte: str
    given_name__in: Collection[str]
    given_name__contains: str
    given_name__startswith: str
    given_name__endswith: str

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

    minimizable: bool
    minimizable__eq: bool
    minimizable__ne: bool
    minimizable__lt: bool
    minimizable__lte: bool
    minimizable__gt: bool
    minimizable__gte: bool
    minimizable__in: Collection[bool]

    mode: str
    mode__eq: str
    mode__ne: str
    mode__lt: str
    mode__lte: str
    mode__gt: str
    mode__gte: str
    mode__in: Collection[str]
    mode__contains: str
    mode__startswith: str
    mode__endswith: str

    active_tab: int
    active_tab__eq: int
    active_tab__ne: int
    active_tab__lt: int
    active_tab__lte: int
    active_tab__gt: int
    active_tab__gte: int
    active_tab__in: Collection[int]

    tabs__url: str
    tabs__url__eq: str
    tabs__url__ne: str
    tabs__url__lt: str
    tabs__url__lte: str
    tabs__url__gt: str
    tabs__url__gte: str
    tabs__url__in: Collection[str]
    tabs__url__contains: str
    tabs__url__startswith: str
    tabs__url__endswith: str

    tabs__title: str
    tabs__title__eq: str
    tabs__title__ne: str
    tabs__title__lt: str
    tabs__title__lte: str
    tabs__title__gt: str
    tabs__title__gte: str
    tabs__title__in: Collection[str]
    tabs__title__contains: str
    tabs__title__startswith: str
    tabs__title__endswith: str

    tabs__loading: bool
    tabs__loading__eq: bool
    tabs__loading__ne: bool
    tabs__loading__lt: bool
    tabs__loading__lte: bool
    tabs__loading__gt: bool
    tabs__loading__gte: bool
    tabs__loading__in: Collection[bool]

    tabs__id: str
    tabs__id__eq: str
    tabs__id__ne: str
    tabs__id__lt: str
    tabs__id__lte: str
    tabs__id__gt: str
    tabs__id__gte: str
    tabs__id__in: Collection[str]
    tabs__id__contains: str
    tabs__id__startswith: str
    tabs__id__endswith: str
