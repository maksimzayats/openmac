from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from typing_extensions import Any, Self

if TYPE_CHECKING:
    from openmac import SafariTab


@dataclass(kw_only=True)
class BasePage:
    _tab: SafariTab

    @classmethod
    def from_tab(cls, tab: SafariTab, **kwargs: Any) -> Self:
        return cls(_tab=tab, **kwargs)


@dataclass(kw_only=True)
class BasePageElement:
    _tab: SafariTab
