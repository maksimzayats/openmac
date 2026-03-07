from __future__ import annotations

from abc import ABC
from dataclasses import dataclass

from appscript import GenericReference

from openmac.apps.browsers.chrome.objects.tabs import ChromeWindowsTabsManager
from openmac.apps.browsers.chrome.objects.windows import ChromeWindowsManager
from openmac.apps.shared.base import BaseApplication


@dataclass(slots=True, kw_only=True)
class BaseBrowser(BaseApplication, ABC):
    ae_browser: GenericReference

    # region Properties

    @property
    def version(self) -> str:
        return self.ae_browser.version()

    @property
    def title(self) -> str:
        return self.ae_browser.title()

    @property
    def frontmost(self) -> bool:
        return self.ae_browser.frontmost()

    # endregion Properties

    # region Managers

    @property
    def windows(self) -> ChromeWindowsManager:
        return ChromeWindowsManager(chrome=self)

    # endregion Managers

    # region Custom Managers

    @property
    def tabs(self) -> ChromeWindowsTabsManager:
        return self.windows.tabs

    # endregion Custom Managers

    # region Actions

    def activate(self) -> None:
        self.ae_browser.activate()

    # endregion Actions
