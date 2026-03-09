from __future__ import annotations

import logging
from dataclasses import dataclass, field

from appscript import GenericReference, Keyword, app

from openmac.apps.browsers.base.objects.application import IBrowser
from openmac.apps.browsers.chrome.objects.bookmark_folders import (
    ChromeBookmarkFolder,
    ChromeBookmarkFoldersManager,
)
from openmac.apps.browsers.chrome.objects.tabs import ChromeWindowsTabsManager
from openmac.apps.browsers.chrome.objects.windows import ChromeWindowsManager
from openmac.apps.shared.base import BaseApplication

logger = logging.getLogger(__name__)


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
    def bookmarks_bar(self) -> ChromeBookmarkFolder:
        return ChromeBookmarkFolder(ae_bookmark_folder=self.ae_chrome.bookmarks_bar())

    @property
    def other_bookmarks(self) -> ChromeBookmarkFolder:
        return ChromeBookmarkFolder(ae_bookmark_folder=self.ae_chrome.other_bookmarks())

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
            bookmarks_bar=ChromeBookmarkFolder(
                ae_bookmark_folder=ae_properties[Keyword("bookmarks_bar")],
            ),
            other_bookmarks=ChromeBookmarkFolder(
                ae_bookmark_folder=ae_properties[Keyword("other_bookmarks")],
            ),
        )

    # endregion Properties

    # region Managers

    @property
    def windows(self) -> ChromeWindowsManager:
        return ChromeWindowsManager(chrome=self)

    # endregion Managers

    # region Custom Managers

    @property
    def bookmark_folders(self) -> ChromeBookmarkFoldersManager:
        return ChromeBookmarkFoldersManager(chrome=self)

    @property
    def tabs(self) -> ChromeWindowsTabsManager:
        return self.windows.tabs

    # endregion Custom Managers

    # region Actions

    def activate(self) -> None:
        logger.info("Activating Chrome")
        self.ae_chrome.activate()

    # endregion Actions


@dataclass(slots=True)
class ChromeProperties:
    version: str
    title: str
    frontmost: bool
    bookmarks_bar: ChromeBookmarkFolder
    other_bookmarks: ChromeBookmarkFolder
