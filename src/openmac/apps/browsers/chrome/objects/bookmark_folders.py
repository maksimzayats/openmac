from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from appscript import GenericReference, Keyword

from openmac.apps.browsers.chrome.objects.bookmark_items import (
    ChromeBookmarkItem,
)
from openmac.apps.shared.base import BaseManager, BaseObject

if TYPE_CHECKING:
    from openmac.apps.browsers.chrome.objects.application import Chrome

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class ChromeBookmarkFolder(BaseObject):
    ae_bookmark_folder: GenericReference = field(repr=False)

    @property
    def id(self) -> str:
        return self.ae_bookmark_folder.id()

    @property
    def title(self) -> str:
        return self.ae_bookmark_folder.title()

    def set_title(self, title: str) -> None:
        logger.info(
            "Renaming Chrome bookmark folder id=%s from %r to %r",
            self.id,
            self.title,
            title,
        )
        self.ae_bookmark_folder.title.set(title)

    @property
    def index(self) -> int:
        return int(self.ae_bookmark_folder.index())

    @property
    def bookmark_folders(self) -> ChromeBookmarkFoldersManager:
        return ChromeBookmarkFoldersManager(folder=self)

    @property
    def bookmark_items(self) -> ChromeBookmarkItemsManager:
        return ChromeBookmarkItemsManager(folder=self)

    @property
    def properties(self) -> ChromeBookmarkFolderProperties:
        ae_properties = self.ae_bookmark_folder.properties()
        return ChromeBookmarkFolderProperties(
            id=ae_properties[Keyword("id")],
            title=ae_properties[Keyword("title")],
            index=ae_properties[Keyword("index")],
        )


@dataclass(slots=True)
class ChromeBookmarkFolderProperties:
    id: str
    title: str
    index: int


@dataclass(slots=True, kw_only=True)
class ChromeBookmarkItemsManager(BaseManager[ChromeBookmarkItem]):
    folder: ChromeBookmarkFolder

    def _iter_objects(self) -> Iterator[ChromeBookmarkItem]:
        logger.debug(
            "Enumerating Chrome bookmark items in folder id=%s title=%r",
            self.folder.id,
            self.folder.title,
        )
        for ae_bookmark_item in self.folder.ae_bookmark_folder.bookmark_items():
            yield ChromeBookmarkItem(
                folder=self.folder,
                ae_bookmark_item=ae_bookmark_item,
            )


@dataclass(slots=True, kw_only=True)
class ChromeBookmarkFoldersManager(BaseManager[ChromeBookmarkFolder]):
    chrome: Chrome | None = None
    folder: ChromeBookmarkFolder | None = None

    def __post_init__(self) -> None:
        if (self.chrome is None) == (self.folder is None):
            msg = "ChromeBookmarkFoldersManager requires exactly one source."
            logger.warning(msg)
            raise ValueError(msg)

    def _iter_objects(self) -> Iterator[ChromeBookmarkFolder]:
        if self.chrome is not None:
            logger.debug("Enumerating top-level Chrome bookmark folders")
            ae_bookmark_folders = self.chrome.ae_chrome.bookmark_folders()
        else:
            folder = self.folder
            if folder is None:
                msg = "ChromeBookmarkFoldersManager requires a folder source."
                logger.warning(msg)
                raise ValueError(msg)
            logger.debug(
                "Enumerating nested Chrome bookmark folders in folder id=%s title=%r",
                folder.id,
                folder.title,
            )
            ae_bookmark_folders = folder.ae_bookmark_folder.bookmark_folders()

        for ae_bookmark_folder in ae_bookmark_folders:
            yield ChromeBookmarkFolder(ae_bookmark_folder=ae_bookmark_folder)
