from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from typing_extensions import Any, Self

if TYPE_CHECKING:
    from openmac import SafariTab


@dataclass(kw_only=True)
class BasePage:
    tab: SafariTab = field(repr=False)

    @classmethod
    def from_tab(cls, tab: SafariTab, **kwargs: Any) -> Self:
        return cls(tab=tab, **kwargs)


@dataclass(kw_only=True)
class BasePageElement:
    tab: SafariTab = field(repr=False)
