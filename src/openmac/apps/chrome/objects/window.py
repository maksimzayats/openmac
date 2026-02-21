from __future__ import annotations

from dataclasses import dataclass

from appscript import Keyword

from openmac.apps._internal.base import BaseManager, BaseObject
from openmac.apps.chrome.objects.tab import Tab, TabsManager


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
        print(ae_properties)
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
        return TabsManager(_objects=[Tab(_ae_object=ae_tab) for ae_tab in self._ae_object.tabs()])


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
    pass
