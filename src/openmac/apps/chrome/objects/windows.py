from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, TypedDict

from appscript import GenericReference, Keyword, k

from openmac.apps._internal.base import BaseManager, BaseObject
from openmac.apps.chrome.objects.tabs import ChromeTab, ChromeTabsManager
from openmac.apps.system_events.helpers import preserve_focus as preserve_focus_context_manager

if TYPE_CHECKING:
    from collections.abc import Collection

    from typing_extensions import Unpack


class ChromeWindow(BaseObject):
    # region Properties

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
    def resizable(self) -> bool:
        return self._ae_object.resizable()

    @property
    def bounds(self) -> list[int]:
        return self._ae_object.bounds()

    @property
    def zoomable(self) -> bool:
        return self._ae_object.zoomable()

    @property
    def minimized(self) -> bool:
        return self._ae_object.minimized()

    @property
    def properties(self) -> ChromeWindowProperties:
        ae_properties = self._ae_object.properties()
        return ChromeWindowProperties(
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
            resizable=ae_properties[Keyword("resizable")],
            bounds=ae_properties[Keyword("bounds")],
            zoomable=ae_properties[Keyword("zoomable")],
            minimized=ae_properties[Keyword("minimized")],
            active_tab=ae_properties[Keyword("active_tab")],
        )

    # endregion Properties

    # region Managers

    @property
    def tabs(self) -> ChromeTabsManager:
        return ChromeTabsManager(
            _from_ae_window=self._ae_object,
            _ae_application=self._ae_application,
            _ae_objects=self._ae_object.tabs,
            _objects=[
                ChromeTab(
                    _ae_application=self._ae_application,
                    _ae_object=ae_tab,
                    _from_ae_window=self._ae_object,
                )
                for ae_tab in self._ae_object.tabs()
            ],
        )

    # endregion Managers

    # region Actions

    def close(self) -> None:
        self._ae_object.close()

    # endregion Actions


@dataclass(slots=True)
class ChromeWindowProperties:
    id: str
    closeable: bool
    zoomed: bool
    active_tab_index: int
    index: int
    visible: bool
    given_name: str
    title: str
    minimizable: bool
    mode: Literal["normal", "incognito"]
    resizable: bool
    bounds: list[int]
    zoomable: bool
    minimized: bool
    active_tab: int


@dataclass(slots=True)
class ChromeWindowsManager(BaseManager[ChromeWindow]):
    if TYPE_CHECKING:

        def get(self, **filters: Unpack[ChromeWindowsFilter]) -> ChromeWindow: ...  # type: ignore[override]
        def filter(self, **filters: Unpack[ChromeWindowsFilter]) -> BaseManager[ChromeWindow]: ...  # type: ignore[override]
        def exclude(self, **filters: Unpack[ChromeWindowsFilter]) -> BaseManager[ChromeWindow]: ...  # type: ignore[override]

    def new(
        self,
        *,
        mode: Literal["normal", "incognito"] = "incognito",
        preserve_focus: bool = True,
    ) -> ChromeWindow:
        if preserve_focus:
            with preserve_focus_context_manager():
                ae_window = self._make_ae_window(mode)
        else:
            ae_window = self._make_ae_window(mode)

        return ChromeWindow(
            _ae_application=self._ae_application,
            _ae_object=ae_window,
        )

    def _make_ae_window(self, mode: Literal["normal", "incognito"]) -> GenericReference:
        return self._ae_application.make(
            new=k.window,
            with_properties={
                Keyword("mode"): mode,
            },
        )


class ChromeWindowsFilter(TypedDict, total=False):
    id: str
    id__eq: str
    id__ne: str
    id__in: Collection[str]
    id__contains: str
    id__startswith: str
    id__endswith: str

    closeable: bool
    closeable__eq: bool
    closeable__ne: bool

    zoomed: bool
    zoomed__eq: bool
    zoomed__ne: bool

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

    given_name: str
    given_name__eq: str
    given_name__ne: str
    given_name__in: Collection[str]
    given_name__contains: str
    given_name__startswith: str
    given_name__endswith: str

    title: str
    title__eq: str
    title__ne: str
    title__in: Collection[str]
    title__contains: str
    title__startswith: str
    title__endswith: str

    minimizable: bool
    minimizable__eq: bool
    minimizable__ne: bool

    mode: Literal["normal", "incognito"]
    mode__eq: Literal["normal", "incognito"]
    mode__ne: Literal["normal", "incognito"]
    mode__in: Collection[Literal["normal", "incognito"]]
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
    tabs__url__in: Collection[str]
    tabs__url__contains: str
    tabs__url__startswith: str
    tabs__url__endswith: str

    tabs__title: str
    tabs__title__eq: str
    tabs__title__ne: str
    tabs__title__in: Collection[str]
    tabs__title__contains: str
    tabs__title__startswith: str
    tabs__title__endswith: str

    tabs__loading: bool
    tabs__loading__eq: bool
    tabs__loading__ne: bool

    tabs__id: str
    tabs__id__eq: str
    tabs__id__ne: str
    tabs__id__in: Collection[str]
    tabs__id__contains: str
    tabs__id__startswith: str
    tabs__id__endswith: str
