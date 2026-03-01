from __future__ import annotations

from collections.abc import Callable
from typing import Any

from openmac.apps.browsers.pages.generic.structure import GenericPage


class GenericPageParser:
    def __init__(self, page_cls: type[GenericPage] = GenericPage) -> None:
        self._page_cls = page_cls

    def parse(
        self,
        source: str,
        javascript_executor: Callable[[str], Any],
    ) -> GenericPage:
        raise NotImplementedError
