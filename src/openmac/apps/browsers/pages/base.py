from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

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

    def real_click(self, selector: str) -> None:
        selector = f"document.querySelector('{selector}')"
        script = REAL_CLICK_FUNCTION + f"\nrealClick({selector});"
        self.tab.execute(script)


@dataclass(kw_only=True)
class BasePageElement:
    pass
