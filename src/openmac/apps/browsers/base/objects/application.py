from __future__ import annotations

from abc import ABC, abstractmethod

from openmac.apps.browsers.base.objects.tabs import IBrowserTab
from openmac.apps.browsers.base.objects.windows import IBrowserWindow
from openmac.apps.shared.base import BaseManager


class IBrowser(ABC):
    # region Properties

    @property
    @abstractmethod
    def version(self) -> str: ...

    @property
    @abstractmethod
    def title(self) -> str: ...

    @property
    @abstractmethod
    def frontmost(self) -> bool: ...

    # endregion Properties

    # region Managers

    @property
    @abstractmethod
    def windows(self) -> BaseManager[IBrowserWindow]: ...

    # endregion Managers

    # region Custom Managers

    @property
    @abstractmethod
    def tabs(self) -> BaseManager[IBrowserTab]: ...

    # endregion Custom Managers

    # region Actions

    @abstractmethod
    def activate(self) -> None: ...

    # endregion Actions
