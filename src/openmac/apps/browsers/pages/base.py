from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup
from typing_extensions import Self  # noqa: UP035

from openmac.apps.browsers.pages.scripts import REAL_CLICK_FUNCTION

if TYPE_CHECKING:
    from openmac.apps.browsers.base.objects.tabs import IBrowserTab


@dataclass(kw_only=True)
class BasePage(ABC):
    tab: IBrowserTab

    @classmethod
    @abstractmethod
    def from_tab(cls, tab: IBrowserTab, **kwargs: Any) -> Self: ...

    @property
    def snapshot(self) -> BeautifulSoup:
        html = self.tab.execute("document.documentElement.outerHTML")
        return BeautifulSoup(html, "lxml")

    def real_click(self, element_getter: str) -> None:
        script = REAL_CLICK_FUNCTION + f"\nrealClick({element_getter});"
        self.tab.execute(script)


@dataclass(kw_only=True)
class BasePageElement:
    pass
