from __future__ import annotations

from dataclasses import dataclass, field

from appscript import GenericReference, Keyword, app

from openmac.apps.browsers.base.objects.application import IBrowser
from openmac.apps.browsers.chrome.objects.tabs import ChromeWindowsTabsManager
from openmac.apps.browsers.chrome.objects.windows import ChromeWindowsManager
from openmac.apps.shared.base import BaseApplication


@dataclass(slots=True, kw_only=True)
class Chrome(BaseApplication, IBrowser):
    ae_chrome: GenericReference = field(default_factory=lambda: app(id="com.google.Chrome"))

    # region Properties

    @property
    def version(self) -> str:
        return self.ae_chrome.version()

    @property
    def title(self) -> str:
        return self.ae_chrome.title()

    @property
    def frontmost(self) -> bool:
        return self.ae_chrome.frontmost()

    @property
    def ae_browser(self) -> GenericReference:
        return self.ae_chrome

    @property
    def properties(self) -> ChromeProperties:
        ae_properties = self.ae_chrome.properties()
        return ChromeProperties(
            version=ae_properties[Keyword("version")],
            title=ae_properties[Keyword("title")],
            frontmost=ae_properties[Keyword("frontmost")],
        )

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
        self.ae_chrome.activate()

    # endregion Actions


@dataclass(slots=True)
class ChromeProperties:
    version: str
    title: str
    frontmost: bool
