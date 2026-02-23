from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from appscript import GenericReference, Keyword, k

from openmac.apps._internal.base import BaseManager, BaseObject
from openmac.apps.chrome.objects.tabs import (
    ChromeWindowsTabsManager,
    ChromeWindowTabsManager,
)
from openmac.apps.system_events.helpers import preserve_focus as preserve_focus_context_manager

if TYPE_CHECKING:
    from openmac import Chrome


@dataclass(slots=True, kw_only=True)
class ChromeWindow(BaseObject):
    ae_window: GenericReference = field(repr=False)

    # region Properties

    @property
    def id(self) -> int:
        return int(self.ae_window.id())

    @property
    def closeable(self) -> bool:
        return self.ae_window.closeable()

    @property
    def zoomed(self) -> bool:
        return self.ae_window.zoomed()

    @property
    def active_tab_index(self) -> int:
        return self.ae_window.active_tab_index()

    @property
    def index(self) -> int:
        return self.ae_window.index()

    @property
    def visible(self) -> bool:
        return self.ae_window.visible()

    @property
    def given_name(self) -> str:
        return self.ae_window.given_name()

    @property
    def title(self) -> str:
        return self.ae_window.title()

    @property
    def minimizable(self) -> bool:
        return self.ae_window.minimizable()

    @property
    def mode(self) -> Literal["normal", "incognito"]:
        return self.ae_window.mode()

    @property
    def resizable(self) -> bool:
        return self.ae_window.resizable()

    @property
    def bounds(self) -> list[int]:
        return self.ae_window.bounds()

    @property
    def zoomable(self) -> bool:
        return self.ae_window.zoomable()

    @property
    def minimized(self) -> bool:
        return self.ae_window.minimized()

    @property
    def properties(self) -> ChromeWindowProperties:
        ae_properties = self.ae_window.properties()
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
    def tabs(self) -> ChromeWindowTabsManager:
        return ChromeWindowTabsManager(from_window=self)

    # endregion Managers

    # region Actions

    def close(self) -> None:
        self.ae_window.close()

    # endregion Actions


@dataclass(slots=True, kw_only=True)
class ChromeWindowProperties:
    id: int
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


@dataclass(slots=True, kw_only=True)
class ChromeWindowsManager(BaseManager[ChromeWindow]):
    chrome: Chrome

    @property
    def tabs(self) -> ChromeWindowsTabsManager:
        return ChromeWindowsTabsManager(from_windows=self)

    def new(
        self,
        *,
        mode: Literal["normal", "incognito"] = "normal",
        preserve_focus: bool = True,
    ) -> ChromeWindow:
        if preserve_focus:
            with preserve_focus_context_manager():
                ae_window = self._make_ae_window(mode)
        else:
            ae_window = self._make_ae_window(mode)

        return ChromeWindow(ae_window=ae_window)

    def _make_ae_window(self, mode: Literal["normal", "incognito"]) -> GenericReference:
        return self.chrome.ae_chrome.make(
            new=k.window,
            with_properties={
                Keyword("mode"): mode,
            },
        )

    def _load(self) -> list[ChromeWindow]:
        return [ChromeWindow(ae_window=ae_window) for ae_window in self.chrome.ae_chrome.windows()]
