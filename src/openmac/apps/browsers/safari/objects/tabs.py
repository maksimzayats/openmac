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
    from openmac.apps.browsers.safari.objects.windows import SafariWindow, SafariWindowsManager

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SafariTab(BaseObject, IBrowserTab):
    window: SafariWindow
    ae_tab: GenericReference

    # region Properties

    @property
    def url(self) -> str:
        return self.ae_tab.URL()

    @property
    def title(self) -> str:
        return self.ae_tab.name()

    def set_url(self, url: str) -> SafariTab:
        logger.info("Setting Safari tab index=%s URL to %s", self.index, url)
        self.ae_tab.URL.set(url)
        return self

    @property
    def index(self) -> int:
        return int(self.ae_tab.index())

    @property
    def text(self) -> str:
        return self.ae_tab.text()

    @property
    def source(self) -> str:
        return cast("str", self.execute("document.documentElement.outerHTML"))

    @property
    def loading(self) -> bool:
        return self.execute("document.readyState") != "complete"

    @property
    def properties(self) -> SafariTabProperties:
        ae_properties = self.ae_tab.properties()
        return SafariTabProperties(
            url=ae_properties[Keyword("URL")],
            title=ae_properties[Keyword("name")],
            index=ae_properties[Keyword("index")],
            text=ae_properties[Keyword("text")],
            source=ae_properties[Keyword("source")],
            loading=self.loading,
        )

    # endregion Properties

    # region Actions

    def reload(self) -> None:
        logger.info("Reloading Safari tab index=%s url=%s", self.index, self.url)
        self.execute("window.location.reload()")

    def close(self) -> None:
        logger.info("Closing Safari tab index=%s url=%s", self.index, self.url)
        self.ae_tab.close()

    def go_back(self) -> None:
        logger.info("Navigating back in Safari tab index=%s url=%s", self.index, self.url)
        self.execute("history.back()")

    def go_forward(self) -> None:
        logger.info("Navigating forward in Safari tab index=%s url=%s", self.index, self.url)
        self.execute("history.forward()")

    def execute(self, javascript: str) -> Any:
        logger.debug(
            "Executing JavaScript in Safari tab index=%s: %s",
            self.index,
            preview_text(javascript),
        )
        result = self.ae_tab.do_JavaScript(javascript)
        if hasattr(result, "AS_name") and result.AS_name == "missing_value":
            logger.debug(
                "JavaScript execution in Safari tab index=%s returned missing value",
                self.index,
            )
            return None

        logger.debug("JavaScript execution in Safari tab index=%s completed", self.index)
        return result

    def email_contents(self) -> None:
        logger.info("Emailing contents of Safari tab index=%s url=%s", self.index, self.url)
        self.ae_tab.email_contents()

    def search_the_web(self, query: str) -> None:
        logger.info("Searching the web from Safari tab index=%s query=%r", self.index, query)
        self.ae_tab.search_the_web(for_=query)

    # endregion Actions

    # region Custom Actions

    def wait_until_loaded(
        self,
        timeout: float = 10.0,
        delay: float = 0.1,
    ) -> None:
        logger.info(
            "Waiting for Safari tab index=%s to finish loading timeout=%s delay=%s url=%s",
            self.index,
            timeout,
            delay,
            self.url,
        )
        start_time = time.perf_counter()
        poll_count = 0

        while True:
            poll_count += 1
            ready_state = self.execute("document.readyState")
            if ready_state == "complete" and self.source:
                logger.info(
                    "Safari tab index=%s finished loading after %s polls",
                    self.index,
                    poll_count,
                )
                return
            if time.perf_counter() - start_time > timeout:
                logger.warning(
                    "Safari tab index=%s timed out while loading after %s seconds",
                    self.index,
                    timeout,
                )
                raise TimeoutError(f"SafariTab did not finish loading within {timeout} seconds.")

            logger.debug(
                "Safari tab index=%s still loading at poll=%s ready_state=%r",
                self.index,
                poll_count,
                ready_state,
            )
            time.sleep(delay)

    def as_page(self, page_cls: type[PageT]) -> PageT:
        logger.info(
            "Casting Safari tab index=%s url=%s to page %s",
            self.index,
            self.url,
            page_cls.__name__,
        )
        return page_cls.from_tab(self)

    # endregion Custom Actions


@dataclass(slots=True)
class SafariTabProperties:
    url: str
    title: str
    index: int
    text: str
    source: str
    loading: bool


@dataclass(slots=True)
class SafariWindowTabsManager(IBrowserTabManager, BaseManager[SafariTab]):
    window: SafariWindow

    @property
    def active(self) -> SafariTab:
        return SafariTab(
            window=self.window,
            ae_tab=self.window.ae_window.current_tab(),
        )

    def open(
        self,
        url: str,
        *,
        wait_until_loaded: bool = True,
        preserve_focus: bool = True,
    ) -> SafariTab:
        logger.info(
            "Opening Safari tab in window id=%s url=%s wait_until_loaded=%s preserve_focus=%s",
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

        tab = SafariTab(
            window=self.window,
            ae_tab=ae_tab,
        )

        if wait_until_loaded:
            tab.wait_until_loaded()

        logger.debug("Opened Safari tab index=%s in window id=%s", tab.index, self.window.id)
        return tab

    def get_or_open(
        self,
        url: str,
        *,
        wait_until_loaded: bool = True,
        preserve_focus: bool = True,
    ) -> SafariTab:
        """Return the first matching tab by URL or open a new tab if no match exists."""
        logger.info(
            "Searching for existing Safari tab in window id=%s url=%s wait_until_loaded=%s",
            self.window.id,
            url,
            wait_until_loaded,
        )
        for tab in self:
            existing_tab = cast("SafariTab", tab)
            if tab.url == url:
                logger.debug(
                    "Found existing Safari tab index=%s for url=%s",
                    existing_tab.index,
                    url,
                )
                if wait_until_loaded:
                    existing_tab.wait_until_loaded()

                return existing_tab

        logger.debug("No existing Safari tab found in window id=%s for url=%s", self.window.id, url)
        return self.open(
            url=url,
            wait_until_loaded=wait_until_loaded,
            preserve_focus=preserve_focus,
        )

    def _make_ae_tab(self, url: str) -> GenericReference:
        logger.debug(
            "Issuing AppleScript request to create Safari tab in window id=%s url=%s",
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
        logger.debug("Enumerating Safari tabs for window id=%s", self.window.id)
        for ae_tab in self.window.ae_window.tabs():
            yield SafariTab(window=self.window, ae_tab=ae_tab)


@dataclass(slots=True)
class SafariWindowsTabsManager(BaseManager[SafariTab]):
    windows: SafariWindowsManager
    only_active: bool = False

    @property
    def active(self) -> SafariWindowsTabsManager:
        return SafariWindowsTabsManager(windows=self.windows, only_active=True)

    def open(
        self,
        url: str,
        *,
        wait_until_loaded: bool = True,
        preserve_focus: bool = True,
    ) -> SafariTab:
        logger.info(
            "Opening Safari tab via windows manager url=%s wait_until_loaded=%s preserve_focus=%s",
            url,
            wait_until_loaded,
            preserve_focus,
        )
        if self.windows.count == 0:
            logger.debug("No Safari windows open; creating a new window for url=%s", url)
            window = self.windows.new(
                url=url,
                preserve_focus=preserve_focus,
            )
            tab = window.current_tab
            if wait_until_loaded:
                tab.wait_until_loaded()

            return tab

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
    ) -> SafariTab:
        """Return the first matching tab across windows or open one if no match exists."""
        logger.info(
            "Searching for existing Safari tab across windows url=%s wait_until_loaded=%s",
            url,
            wait_until_loaded,
        )
        for tab in self:
            if tab.url == url:
                logger.debug(
                    "Found existing Safari tab index=%s across windows for url=%s",
                    tab.index,
                    url,
                )
                if wait_until_loaded:
                    tab.wait_until_loaded()

                return tab

        logger.debug("No existing Safari tab found across windows for url=%s", url)
        return self.open(
            url=url,
            wait_until_loaded=wait_until_loaded,
            preserve_focus=preserve_focus,
        )

    def _iter_objects(self) -> Any:
        logger.debug("Enumerating Safari tabs across windows only_active=%s", self.only_active)
        for window in self.windows:
            if self.only_active:
                yield window.tabs.active
                continue

            for ae_tab in window.ae_window.tabs():
                yield SafariTab(
                    window=window,
                    ae_tab=ae_tab,
                )
