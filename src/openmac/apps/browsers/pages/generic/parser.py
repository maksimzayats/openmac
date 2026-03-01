from __future__ import annotations

from openmac.apps.browsers.pages.generic.structure import GenericPage


class GenericPageParser:
    def __init__(self, page_cls: type[GenericPage] = GenericPage) -> None:
        self._page_cls = page_cls

    def parse(self, source: str) -> GenericPage:
        raise NotImplementedError
