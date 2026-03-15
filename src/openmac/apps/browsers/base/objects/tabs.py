from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from openmac.apps.shared.base import BaseManager

if TYPE_CHECKING:
    from openmac import IBrowserWindow


class IBrowserTab(ABC):
    window: IBrowserWindow

    # region Properties

    @property
    @abstractmethod
    def url(self) -> str: ...

    @abstractmethod
    def set_url(self, url: str) -> IBrowserTab: ...

    @property
    @abstractmethod
    def title(self) -> str: ...

    @property
    @abstractmethod
    def loading(self) -> bool: ...

    # endregion Properties

    # region Actions

    @abstractmethod
    def reload(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def go_back(self) -> None: ...

    @abstractmethod
    def go_forward(self) -> None: ...

    @abstractmethod
    def execute(self, javascript: str) -> Any: ...

    # endregion Actions

    # region Custom Actions

    @property
    @abstractmethod
    def source(self) -> str: ...

    @abstractmethod
    def wait_until_loaded(
        self,
        timeout: float = 10.0,
        delay: float = 0.1,
    ) -> None: ...

    # endregion Custom Actions


class IBrowserTabManager(BaseManager[IBrowserTab], ABC):
    window: IBrowserWindow

    # region Actions

    @abstractmethod
    def open(
        self,
        url: str,
        *,
        wait_until_loaded: bool = True,
        preserve_focus: bool = True,
    ) -> IBrowserTab: ...

    # endregion Actions
