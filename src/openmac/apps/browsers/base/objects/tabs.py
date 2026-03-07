from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IBrowserTab(ABC):
    # region Properties

    @property
    @abstractmethod
    def url(self) -> str: ...

    @abstractmethod
    def set_url(self, url: str) -> None: ...

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
