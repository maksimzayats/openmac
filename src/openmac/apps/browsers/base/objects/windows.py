from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from openmac.apps.browsers.base.objects.tabs import IBrowserTabManager


class IBrowserWindow(ABC):
    # region Properties

    @property
    @abstractmethod
    def visible(self) -> bool: ...

    @property
    @abstractmethod
    def title(self) -> str: ...

    @property
    @abstractmethod
    def mode(self) -> Literal["normal", "incognito"]: ...

    # endregion Properties

    # region Managers

    @property
    @abstractmethod
    def tabs(self) -> IBrowserTabManager: ...

    # endregion Managers

    # region Actions

    @abstractmethod
    def close(self) -> None: ...

    # endregion Actions
