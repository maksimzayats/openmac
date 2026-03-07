from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from typing_extensions import Self  # noqa: UP035

if TYPE_CHECKING:
    from openmac.apps.browsers.base.objects.tabs import IBrowserTab


class BasePage(ABC):
    @classmethod
    @abstractmethod
    def from_tab(cls, tab: IBrowserTab, **kwargs: Any) -> Self: ...


class BasePageElement:
    pass
