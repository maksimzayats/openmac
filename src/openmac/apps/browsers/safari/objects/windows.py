from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from appscript import GenericReference, Keyword, k

from openmac.apps.browsers.base.objects.windows import IBrowserWindow, IBrowserWindowsManager
from openmac.apps.browsers.safari.objects.tabs import (
    SafariTab,
    SafariWindowsTabsManager,
    SafariWindowTabsManager,
)
from openmac.apps.shared.base import BaseManager, BaseObject
from openmac.apps.system_events.helpers import preserve_focus as preserve_focus_context_manager

if TYPE_CHECKING:
    from openmac.apps.browsers.safari.objects.application import Safari


@dataclass(slots=True, kw_only=True)
class SafariWindow(BaseObject, IBrowserWindow):
    ae_window: GenericReference = field(repr=False)

    # region Properties

    @property
    def id(self) -> int:
        return int(self.ae_window.id())

    @property
    def name(self) -> str:
        return self.ae_window.name()

    @property
    def title(self) -> str:
        return self.name

    @property
    def index(self) -> int:
        return int(self.ae_window.index())

    @property
    def bounds(self) -> list[int]:
        return list(self.ae_window.bounds())

    @property
    def closeable(self) -> bool:
        return self.ae_window.closeable()

    @property
    def miniaturizable(self) -> bool:
        return self.ae_window.miniaturizable()

    @property
    def miniaturized(self) -> bool:
        return self.ae_window.miniaturized()

    @property
    def resizable(self) -> bool:
        return self.ae_window.resizable()

    @property
    def visible(self) -> bool:
        return self.ae_window.visible()

    @property
    def mode(self) -> Literal["normal", "incognito"]:
        return "normal"

    @property
    def zoomable(self) -> bool:
        return self.ae_window.zoomable()

    @property
    def zoomed(self) -> bool:
        return self.ae_window.zoomed()

    @property
    def current_tab(self) -> SafariTab:
        return SafariTab(
            window=self,
            ae_tab=self.ae_window.current_tab(),
        )

    # endregion Properties

    # region Managers

    @property
    def tabs(self) -> SafariWindowTabsManager:
        return SafariWindowTabsManager(window=self)

    # endregion Managers

    # region Actions

    def close(self) -> None:
        self.ae_window.close()

    # endregion Actions


@dataclass(slots=True, kw_only=True)
class SafariWindowsManager(BaseManager[SafariWindow], IBrowserWindowsManager):
    safari: Safari

    @property
    def tabs(self) -> SafariWindowsTabsManager:
        return SafariWindowsTabsManager(windows=self)

    def new(
        self,
        *,
        url: str | None = None,
        preserve_focus: bool = True,
    ) -> SafariWindow:
        if preserve_focus:
            with preserve_focus_context_manager():
                ae_window = self._make_ae_window(url)
        else:
            ae_window = self._make_ae_window(url)

        return SafariWindow(ae_window=ae_window)

    def _make_ae_window(self, url: str | None) -> GenericReference:
        command_kwargs: dict[str, dict[Keyword, str]] = {}
        if url is not None:
            command_kwargs["with_properties"] = {Keyword("URL"): url}

        self.safari.ae_safari.make(new=k.document, **command_kwargs)
        return self.safari.ae_safari.windows.first

    def _iter_objects(self) -> Iterator[SafariWindow]:
        for ae_window in self.safari.ae_safari.windows():
            yield SafariWindow(ae_window=ae_window)
