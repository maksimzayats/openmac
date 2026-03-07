from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from appscript import GenericReference, Keyword, k

from openmac.apps.browsers.base.objects.tabs import IBrowserTab, PageT
from openmac.apps.shared.base import BaseManager, BaseObject
from openmac.apps.system_events.helpers import preserve_focus as preserve_focus_context_manager

if TYPE_CHECKING:
    from openmac.apps.browsers.chrome.objects.windows import ChromeWindow, ChromeWindowsManager


@dataclass(slots=True)
class ChromeTab(BaseObject, IBrowserTab):
    window: ChromeWindow
    ae_tab: GenericReference

    # region Properties

    @property
    def url(self) -> str:
        return self.ae_tab.URL()

    def set_url(self, url: str) -> ChromeTab:
        self.ae_tab.URL.set(url)
        return self

    @property
    def title(self) -> str:
        return self.ae_tab.title()

    @property
    def loading(self) -> bool:
        return self.ae_tab.loading()

    @property
    def id(self) -> int:
        return int(self.ae_tab.id())

    @property
    def properties(self) -> ChromeTabProperties:
        ae_properties = self.ae_tab.properties()
        return ChromeTabProperties(
            url=ae_properties[Keyword("URL")],
            title=ae_properties[Keyword("title")],
            loading=ae_properties[Keyword("loading")],
            id=ae_properties[Keyword("id")],
        )

    # endregion Properties

    # region Actions

    def reload(self) -> None:
        self.ae_tab.reload()

    def close(self) -> None:
        self.ae_tab.close()

    def go_back(self) -> None:
        self.ae_tab.go_back()

    def go_forward(self) -> None:
        self.ae_tab.go_forward()

    def duplicate(self) -> ChromeTab:
        ae_tab = self.window.ae_window.tabs.end.make(
            new=k.tab,
            with_properties={
                Keyword("URL"): self.url,
            },
        )

        return ChromeTab(
            ae_tab=ae_tab,
            window=self.window,
        )

    def execute(self, javascript: str) -> Any | None:
        result = self.ae_tab.execute(javascript=javascript)
        if hasattr(result, "AS_name") and result.AS_name == "missing_value":
            return None

        return result

    # endregion Actions

    # region Custom Actions

    @property
    def source(self) -> str:
        return cast("str", self.execute("document.documentElement.outerHTML"))

    @property
    def html(self) -> str:
        return self.source

    def wait_until_loaded(
        self,
        timeout: float = 10.0,
        delay: float = 0.1,
    ) -> None:
        start_time = time.perf_counter()

        while self.loading:
            if time.perf_counter() - start_time > timeout:
                raise TimeoutError(f"ChromeTab did not finish loading within {timeout} seconds.")

            time.sleep(delay)

    def as_page(self, page_cls: type[PageT]) -> PageT:
        return page_cls.from_tab(self)

    # endregion Custom Actions


@dataclass(slots=True)
class ChromeTabProperties:
    id: int
    url: str
    title: str
    loading: bool


@dataclass(slots=True)
class ChromeWindowTabsManager(BaseManager[ChromeTab]):
    window: ChromeWindow

    @property
    def active(self) -> ChromeTab:
        return ChromeTab(
            window=self.window,
            ae_tab=self.window.ae_window.active_tab(),
        )

    def open(
        self,
        url: str,
        *,
        wait_until_loaded: bool = True,
        preserve_focus: bool = True,
    ) -> ChromeTab:
        if preserve_focus:
            with preserve_focus_context_manager():
                ae_tab = self._make_ae_tab(url)
        else:
            ae_tab = self._make_ae_tab(url)

        tab = ChromeTab(
            window=self.window,
            ae_tab=ae_tab,
        )

        if wait_until_loaded:
            tab.wait_until_loaded()

        return tab

    def get_or_open(
        self,
        url: str,
        *,
        wait_until_loaded: bool = True,
        preserve_focus: bool = True,
    ) -> ChromeTab:
        """Return the first matching tab by URL or open a new tab if no match exists."""
        for tab in self:
            if tab.url == url:
                if wait_until_loaded:
                    tab.wait_until_loaded()

                return tab

        return self.open(
            url=url,
            wait_until_loaded=wait_until_loaded,
            preserve_focus=preserve_focus,
        )

    def _make_ae_tab(self, url: str) -> GenericReference:
        return self.window.ae_window.tabs.end.make(
            new=k.tab,
            with_properties={
                Keyword("URL"): url,
            },
        )

    def _iter_objects(self) -> Any:
        for ae_tab in self.window.ae_window.tabs():
            yield ChromeTab(window=self.window, ae_tab=ae_tab)


@dataclass(slots=True)
class ChromeWindowsTabsManager(BaseManager[ChromeTab]):
    windows: ChromeWindowsManager
    only_active: bool = False

    @property
    def active(self) -> ChromeWindowsTabsManager:
        return ChromeWindowsTabsManager(windows=self.windows, only_active=True)

    def open(
        self,
        url: str,
        *,
        wait_until_loaded: bool = True,
        preserve_focus: bool = True,
    ) -> ChromeTab:
        return self.windows.first.tabs.open(
            url=url,
            wait_until_loaded=wait_until_loaded,
            preserve_focus=preserve_focus,
        )

    def get_or_open(
        self,
        url: str,
        *,
        wait_until_loaded: bool = True,
        preserve_focus: bool = True,
    ) -> ChromeTab:
        """Return the first matching tab across windows or open one in the first window."""
        for tab in self:
            if tab.url == url:
                if wait_until_loaded:
                    tab.wait_until_loaded()

                return tab

        return self.open(
            url=url,
            wait_until_loaded=wait_until_loaded,
            preserve_focus=preserve_focus,
        )

    def _iter_objects(self) -> Any:
        for window in self.windows:
            if self.only_active:
                yield window.tabs.active
                continue

            for ae_tab in window.ae_window.tabs():
                yield ChromeTab(
                    window=window,
                    ae_tab=ae_tab,
                )
