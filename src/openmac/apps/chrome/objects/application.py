from __future__ import annotations

from dataclasses import dataclass

from appscript import Keyword

from openmac.apps._internal.base import BaseApplication
from openmac.apps.chrome.objects.bookmarks_folders import (
    BookmarkFolders,
    BookmarkFoldersManager,
)
from openmac.apps.chrome.objects.windows import Window, WindowsManager


class Chrome(BaseApplication):
    _BUNDLE_ID = "com.google.Chrome"

    # region Properties

    @property
    def version(self) -> str:
        return self._ae_object.version()

    @property
    def title(self) -> str:
        return self._ae_object.title()

    @property
    def frontmost(self) -> bool:
        return self._ae_object.frontmost()

    @property
    def properties(self) -> ChromeProperties:
        ae_properties = self._ae_object.properties()
        return ChromeProperties(
            version=ae_properties[Keyword("version")],
            title=ae_properties[Keyword("title")],
            frontmost=ae_properties[Keyword("frontmost")],
        )

    # endregion Properties

    # region Managers

    @property
    def windows(self) -> WindowsManager:
        return WindowsManager(
            _ae_application=self._ae_object,
            _ae_objects=self._ae_object.windows,
            _objects=[
                Window(_ae_application=self._ae_object, _ae_object=ae_window)
                for ae_window in self._ae_object.windows()
            ],
        )

    @property
    def bookmark_folders(self) -> BookmarkFoldersManager:
        return BookmarkFoldersManager(
            _ae_application=self._ae_object,
            _ae_objects=self._ae_object.bookmarks_bar,
            _objects=[
                BookmarkFolders(_ae_application=self._ae_object, _ae_object=ae_bookmarks_bar)
                for ae_bookmarks_bar in self._ae_object.bookmark_folders()
            ],
        )

    # endregion Managers

    # region Actions

    def activate(self) -> None:
        self._ae_object.activate()

    # endregion Actions


@dataclass(slots=True)
class ChromeProperties:
    version: str
    title: str
    frontmost: bool
