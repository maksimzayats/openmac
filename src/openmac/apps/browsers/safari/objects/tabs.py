from __future__ import annotations

import time
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, TypeVar

from appscript import GenericReference, Keyword, k

from openmac.apps._internal.base import BaseManager, BaseObject
from openmac.apps.browsers.pages.base import BasePage
from openmac.apps.system_events.helpers import preserve_focus as preserve_focus_context_manager

if TYPE_CHECKING:
    from openmac import SafariWindow
    from openmac.apps.browsers.safari.objects.windows import SafariWindowsManager


PageT = TypeVar("PageT", bound=BasePage)


@dataclass(slots=True)
class SafariTab(BaseObject):
    from_window: SafariWindow
    ae_tab: GenericReference

    # region Properties

    @property
    def url(self) -> str:
        return self.ae_tab.URL()

    @property
    def name(self) -> str:
        return self.ae_tab.name()

    @property
    def index(self) -> int:
        return int(self.ae_tab.index())

    @property
    def text(self) -> str:
        return self.ae_tab.text()

    @property
    def source(self) -> str:
        return self.ae_tab.source()

    @property
    def visible(self) -> bool:
        return self.ae_tab.visible()

    @property
    def properties(self) -> SafariTabProperties:
        ae_properties = self.ae_tab.properties()
        return SafariTabProperties(
            url=ae_properties[Keyword("URL")],
            name=ae_properties[Keyword("name")],
            index=ae_properties[Keyword("index")],
            text=ae_properties[Keyword("text")],
            source=ae_properties[Keyword("source")],
            visible=ae_properties[Keyword("visible")],
        )

    # endregion Properties

    # region Actions

    def close(self) -> None:
        self.ae_tab.close()

    def execute(self, javascript: str) -> Any:
        result = self.ae_tab.do_JavaScript(javascript)
        if hasattr(result, "AS_name") and result.AS_name == "missing_value":
            return None

        return result

    def email_contents(self) -> None:
        self.ae_tab.email_contents()

    def search_the_web(self, query: str) -> None:
        self.ae_tab.search_the_web(for_=query)

    # endregion Actions

    # region Custom Actions

    def wait_until_loaded(
        self,
        timeout: float = 10.0,
        delay: float = 0.1,
    ) -> None:
        start_time = time.perf_counter()

        while True:
            ready_state = self.execute("document.readyState")
            if ready_state == "complete" and self.source:
                return
            if time.perf_counter() - start_time > timeout:
                raise TimeoutError(f"SafariTab did not finish loading within {timeout} seconds.")

            time.sleep(delay)

    def as_page(
        self,
        page_class: type[PageT],
        **kwargs: Any,
    ) -> PageT:
        return page_class.from_tab(tab=self, **kwargs)

    # endregion Custom Actions


@dataclass(slots=True)
class SafariTabProperties:
    url: str
    name: str
    index: int
    text: str
    source: str
    visible: bool


@dataclass(slots=True)
class SafariWindowTabsManager(BaseManager[SafariTab]):
    from_window: SafariWindow

    @property
    def active(self) -> SafariTab:
        return SafariTab(
            from_window=self.from_window,
            ae_tab=self.from_window.ae_window.current_tab(),
        )

    def open(
        self,
        url: str,
        *,
        wait_until_loaded: bool = True,
        preserve_focus: bool = True,
    ) -> SafariTab:
        if preserve_focus:
            with preserve_focus_context_manager():
                ae_tab = self._make_ae_tab(url)
        else:
            ae_tab = self._make_ae_tab(url)

        tab = SafariTab(
            from_window=self.from_window,
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
    ) -> SafariTab:
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
        return self.from_window.ae_window.tabs.end.make(
            new=k.tab,
            with_properties={
                Keyword("URL"): url,
            },
        )

    def _load(self) -> list[SafariTab]:
        return [
            SafariTab(from_window=self.from_window, ae_tab=ae_tab)
            for ae_tab in self.from_window.ae_window.tabs()
        ]


@dataclass(slots=True)
class SafariWindowsTabsManager(BaseManager[SafariTab]):
    from_windows: SafariWindowsManager

    @property
    def active(self) -> SafariWindowsTabsManager:
        active_tabs = [window.tabs.active for window in self.from_windows]

        return replace(self, _loaded_objects=active_tabs, _loaded=True)

    def open(
        self,
        url: str,
        *,
        wait_until_loaded: bool = True,
        preserve_focus: bool = True,
    ) -> SafariTab:
        if self.from_windows.count == 0:
            window = self.from_windows.new(
                url=url,
                preserve_focus=preserve_focus,
            )
            tab = window.current_tab
            if wait_until_loaded:
                tab.wait_until_loaded()

            return tab

        return self.from_windows.first.tabs.open(
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

    def _load(self) -> list[SafariTab]:
        return [
            SafariTab(
                from_window=window,
                ae_tab=ae_tab,
            )
            for window in self.from_windows
            for ae_tab in window.ae_window.tabs()
        ]
