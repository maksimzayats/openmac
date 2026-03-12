from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from appscript import GenericReference, Keyword, k

from openmac._logging import preview_text
from openmac.apps.browsers.base.objects.tabs import IBrowserTab, IBrowserTabManager, PageT
from openmac.apps.shared.base import BaseManager, BaseObject
from openmac.apps.system_events.helpers import preserve_focus as preserve_focus_context_manager

if TYPE_CHECKING:
    from openmac.apps.browsers.chrome.objects.windows import ChromeWindow, ChromeWindowsManager

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ChromeTab(BaseObject, IBrowserTab):
    window: ChromeWindow
    ae_tab: GenericReference

    # region Properties

    @property
    def url(self) -> str:
        return self.ae_tab.URL()

    def set_url(self, url: str) -> ChromeTab:
        logger.info("Setting Chrome tab id=%s URL to %s", self.id, url)
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
        logger.info("Reloading Chrome tab id=%s url=%s", self.id, self.url)
        self.ae_tab.reload()

    def close(self) -> None:
        logger.info("Closing Chrome tab id=%s url=%s", self.id, self.url)
        self.ae_tab.close()

    def go_back(self) -> None:
        logger.info("Navigating back in Chrome tab id=%s url=%s", self.id, self.url)
        self.ae_tab.go_back()

    def go_forward(self) -> None:
        logger.info("Navigating forward in Chrome tab id=%s url=%s", self.id, self.url)
        self.ae_tab.go_forward()

    def duplicate(self) -> ChromeTab:
        logger.info("Duplicating Chrome tab id=%s url=%s", self.id, self.url)
        ae_tab = self.window.ae_window.tabs.end.make(
            new=k.tab,
            with_properties={
                Keyword("URL"): self.url,
            },
        )

        duplicated_tab = ChromeTab(
            ae_tab=ae_tab,
            window=self.window,
        )
        logger.debug(
            "Created duplicate Chrome tab id=%s from source id=%s",
            duplicated_tab.id,
            self.id,
        )
        return duplicated_tab

    def execute(self, javascript: str) -> Any | None:
        logger.debug(
            "Executing JavaScript in Chrome tab id=%s: %s",
            self.id,
            preview_text(javascript),
        )
        result = self.ae_tab.execute(javascript=javascript)
        if hasattr(result, "AS_name") and result.AS_name == "missing_value":
            logger.debug("JavaScript execution in Chrome tab id=%s returned missing value", self.id)
            return None

        logger.debug("JavaScript execution in Chrome tab id=%s completed", self.id)
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
        logger.info(
            "Waiting for Chrome tab id=%s to finish loading timeout=%s delay=%s url=%s",
            self.id,
            timeout,
            delay,
            self.url,
        )
        start_time = time.perf_counter()
        poll_count = 0

        while self.loading:
            poll_count += 1
            logger.debug("Chrome tab id=%s still loading at poll=%s", self.id, poll_count)
            if time.perf_counter() - start_time > timeout:
                logger.warning(
                    "Chrome tab id=%s timed out while loading after %s seconds",
                    self.id,
                    timeout,
                )
                raise TimeoutError(f"ChromeTab did not finish loading within {timeout} seconds.")

            time.sleep(delay)

        logger.info("Chrome tab id=%s finished loading after %s polls", self.id, poll_count)

    def as_page(self, page_cls: type[PageT]) -> PageT:
        logger.info(
            "Casting Chrome tab id=%s url=%s to page %s",
            self.id,
            self.url,
            page_cls.__name__,
        )
        return page_cls.from_tab(self)

    # endregion Custom Actions


@dataclass(slots=True)
class ChromeTabProperties:
    id: int
    url: str
    title: str
    loading: bool


@dataclass(slots=True)
class ChromeWindowTabsManager(IBrowserTabManager, BaseManager[ChromeTab]):
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
        logger.info(
            "Opening Chrome tab in window id=%s url=%s wait_until_loaded=%s preserve_focus=%s",
            self.window.id,
            url,
            wait_until_loaded,
            preserve_focus,
        )
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

        logger.debug("Opened Chrome tab id=%s in window id=%s", tab.id, self.window.id)
        return tab

    def get_or_open(
        self,
        url: str,
        *,
        wait_until_loaded: bool = True,
        preserve_focus: bool = True,
    ) -> ChromeTab:
        """Return the first matching tab by URL or open a new tab if no match exists."""
        logger.info(
            "Searching for existing Chrome tab in window id=%s url=%s wait_until_loaded=%s",
            self.window.id,
            url,
            wait_until_loaded,
        )
        for tab in self:
            existing_tab = cast("ChromeTab", tab)
            if tab.url == url:
                logger.debug("Found existing Chrome tab id=%s for url=%s", existing_tab.id, url)
                if wait_until_loaded:
                    existing_tab.wait_until_loaded()

                return existing_tab

        logger.debug("No existing Chrome tab found in window id=%s for url=%s", self.window.id, url)
        return self.open(
            url=url,
            wait_until_loaded=wait_until_loaded,
            preserve_focus=preserve_focus,
        )

    def _make_ae_tab(self, url: str) -> GenericReference:
        logger.debug(
            "Issuing AppleScript request to create Chrome tab in window id=%s url=%s",
            self.window.id,
            url,
        )
        return self.window.ae_window.tabs.end.make(
            new=k.tab,
            with_properties={
                Keyword("URL"): url,
            },
        )

    def _iter_objects(self) -> Any:
        logger.debug("Enumerating Chrome tabs for window id=%s", self.window.id)
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
        logger.info(
            "Opening Chrome tab via windows manager url=%s wait_until_loaded=%s preserve_focus=%s",
            url,
            wait_until_loaded,
            preserve_focus,
        )
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
        logger.info(
            "Searching for existing Chrome tab across windows url=%s wait_until_loaded=%s",
            url,
            wait_until_loaded,
        )
        for tab in self:
            if tab.url == url:
                logger.debug(
                    "Found existing Chrome tab id=%s across windows for url=%s",
                    tab.id,
                    url,
                )
                if wait_until_loaded:
                    tab.wait_until_loaded()

                return tab

        logger.debug("No existing Chrome tab found across windows for url=%s", url)
        return self.open(
            url=url,
            wait_until_loaded=wait_until_loaded,
            preserve_focus=preserve_focus,
        )

    def _iter_objects(self) -> Any:
        logger.debug("Enumerating Chrome tabs across windows only_active=%s", self.only_active)
        for window in self.windows:
            if self.only_active:
                yield window.tabs.active
                continue

            for ae_tab in window.ae_window.tabs():
                yield ChromeTab(
                    window=window,
                    ae_tab=ae_tab,
                )
