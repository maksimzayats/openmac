from __future__ import annotations

from abc import ABC, abstractmethod

from openmac.apps.browsers.base.objects.tabs import IBrowserTabsManager
from openmac.apps.browsers.base.objects.windows import IBrowserWindowsManager


class IBrowser[
    BrowserWindowsManagerT: IBrowserWindowsManager,
    BrowserTabsManagerT: IBrowserTabsManager,
](ABC):
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
    def windows(self) -> BrowserWindowsManagerT: ...

    # endregion Managers

    # region Custom Managers

    @property
    @abstractmethod
    def tabs(self) -> BrowserTabsManagerT: ...

    # endregion Custom Managers

    # region Actions

    @abstractmethod
    def activate(self) -> None: ...

    # endregion Actions
