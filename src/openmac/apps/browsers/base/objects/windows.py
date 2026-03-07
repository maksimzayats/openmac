from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, get_args

from appscript import GenericReference, Keyword, k

from openmac.apps.shared.base import BaseManager, BaseObject
from openmac.apps.system_events.helpers import preserve_focus as preserve_focus_context_manager

if TYPE_CHECKING:
    from openmac.apps.browsers.base.objects.application import BaseBrowser


@dataclass(slots=True, kw_only=True)
class BaseBrowserWindow(BaseObject):
    ae_window: GenericReference = field(repr=False)

    # region Properties

    @property
    def visible(self) -> bool:
        return self.ae_window.visible()

    @property
    def title(self) -> str:
        return self.ae_window.title()

    @property
    def mode(self) -> Literal["normal", "incognito"]:
        return self.ae_window.mode()

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
class BaseBrowserWindowsManager(BaseManager[BaseBrowserWindow]):
    browser: BaseBrowser

    @property
    def tabs(self) -> ChromeWindowsTabsManager:
        return ChromeWindowsTabsManager(from_windows=self)

    def new(
        self,
        *,
        mode: Literal["normal", "incognito"] = "normal",
        preserve_focus: bool = True,
    ) -> BaseBrowserWindow:
        if preserve_focus:
            with preserve_focus_context_manager():
                ae_window = self._make_ae_window(mode)
        else:
            ae_window = self._make_ae_window(mode)

        return self._window_class(ae_window=ae_window)

    def _make_ae_window(self, mode: Literal["normal", "incognito"]) -> GenericReference:
        return self.chrome.ae_browser.make(
            new=k.window,
            with_properties={
                Keyword("mode"): mode,
            },
        )

    def _load(self) -> list[ChromeWindow]:
        return [ChromeWindow(ae_window=ae_window) for ae_window in self.chrome.ae_browser.windows()]

    @property
    def _window_class(self) -> type[BaseBrowserWindow]:
        orig_class = self.__orig_class__
        return get_args(orig_class)[0]
