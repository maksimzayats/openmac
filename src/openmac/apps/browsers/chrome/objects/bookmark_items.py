from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from appscript import GenericReference, Keyword

from openmac.apps.shared.base import BaseObject

if TYPE_CHECKING:
    from openmac.apps.browsers.chrome.objects.bookmark_folders import ChromeBookmarkFolder

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class ChromeBookmarkItem(BaseObject):
    folder: ChromeBookmarkFolder = field(repr=False)
    ae_bookmark_item: GenericReference = field(repr=False)

    @property
    def id(self) -> str:
        return self.ae_bookmark_item.id()

    @property
    def title(self) -> str:
        return self.ae_bookmark_item.title()

    def set_title(self, title: str) -> None:
        logger.info("Renaming Chrome bookmark item id=%s from %r to %r", self.id, self.title, title)
        self.ae_bookmark_item.title.set(title)

    @property
    def url(self) -> str:
        return self.ae_bookmark_item.URL()

    def set_url(self, url: str) -> None:
        logger.info("Updating Chrome bookmark item id=%s URL to %s", self.id, url)
        self.ae_bookmark_item.URL.set(url)

    @property
    def index(self) -> int:
        return int(self.ae_bookmark_item.index())

    @property
    def properties(self) -> ChromeBookmarkItemProperties:
        ae_properties = self.ae_bookmark_item.properties()
        return ChromeBookmarkItemProperties(
            id=ae_properties[Keyword("id")],
            title=ae_properties[Keyword("title")],
            url=ae_properties[Keyword("URL")],
            index=ae_properties[Keyword("index")],
        )


@dataclass(slots=True)
class ChromeBookmarkItemProperties:
    id: str
    title: str
    url: str
    index: int
