from __future__ import annotations

import time
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, TypedDict

from appscript import GenericReference, Keyword, k

from openmac.apps._internal.base import BaseManager, BaseObject
from openmac.apps.system_events.helpers import preserve_focus as preserve_focus_context_manager

if TYPE_CHECKING:
    from collections.abc import Collection

    from typing_extensions import Unpack

    from openmac import ChromeWindow
    from openmac.apps.chrome.objects.windows import ChromeWindowsManager


@dataclass(slots=True)
class ChromeTab(BaseObject):
    from_window: ChromeWindow
    ae_tab: GenericReference

    # region Properties

    @property
    def url(self) -> str:
        return self.ae_tab.URL()

    @property
    def title(self) -> str:
        return self.ae_tab.title()

    @property
    def loading(self) -> bool:
        return self.ae_tab.loading()

    @property
    def id(self) -> str:
        return self.ae_tab.id()

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
        ae_tab = self.from_window.ae_window.tabs.end.make(
            new=k.tab,
            with_properties={
                Keyword("URL"): self.url,
            },
        )

        return ChromeTab(
            ae_tab=ae_tab,
            from_window=self.from_window,
        )

    def execute(self, javascript: str) -> str:
        return self.ae_tab.execute(javascript=javascript)

    # endregion Actions

    # region Custom Actions

    @property
    def source(self) -> str:
        return self.execute("document.documentElement.outerHTML")

    def wait_until_loaded(self, timeout: float = 10.0) -> None:
        start_time = time.perf_counter()

        while self.loading:
            if time.perf_counter() - start_time > timeout:
                raise TimeoutError(f"ChromeTab did not finish loading within {timeout} seconds.")

            time.sleep(0.1)

    # endregion Custom Actions


@dataclass(slots=True)
class ChromeTabProperties:
    url: str
    title: str
    loading: bool
    id: str


@dataclass(slots=True)
class ChromeWindowTabsManager(BaseManager[ChromeTab]):
    from_window: ChromeWindow

    if TYPE_CHECKING:

        def get(self, **filters: Unpack[ChromeTabsFilter]) -> ChromeTab: ...  # type: ignore[override]
        def filter(self, **filters: Unpack[ChromeTabsFilter]) -> BaseManager[ChromeTab]: ...  # type: ignore[override]
        def exclude(self, **filters: Unpack[ChromeTabsFilter]) -> BaseManager[ChromeTab]: ...  # type: ignore[override]

    @property
    def active(self) -> ChromeTab:
        return ChromeTab(
            from_window=self.from_window,
            ae_tab=self.from_window.ae_window.active_tab(),
        )

    def new(
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
            from_window=self.from_window,
            ae_tab=ae_tab,
        )

        if wait_until_loaded:
            tab.wait_until_loaded()

        return tab

    def _make_ae_tab(self, url: str) -> GenericReference:
        return self.from_window.ae_window.tabs.end.make(
            new=k.tab,
            with_properties={
                Keyword("URL"): url,
            },
        )

    def _load(self) -> list[ChromeTab]:
        return [
            ChromeTab(from_window=self.from_window, ae_tab=ae_tab)
            for ae_tab in self.from_window.ae_window.tabs()
        ]


@dataclass(slots=True)
class ChromeWindowsTabsManager(BaseManager[ChromeTab]):
    from_windows: ChromeWindowsManager

    if TYPE_CHECKING:

        def get(self, **filters: Unpack[ChromeTabsFilter]) -> ChromeTab: ...  # type: ignore[override]
        def filter(self, **filters: Unpack[ChromeTabsFilter]) -> BaseManager[ChromeTab]: ...  # type: ignore[override]
        def exclude(self, **filters: Unpack[ChromeTabsFilter]) -> BaseManager[ChromeTab]: ...  # type: ignore[override]

    @property
    def active(self) -> ChromeWindowsTabsManager:
        active_tabs = [window.tabs.active for window in self.from_windows]

        return replace(self, __objects=active_tabs, _loaded=True)

    def _load(self) -> list[ChromeTab]:
        return [
            ChromeTab(
                from_window=window,
                ae_tab=ae_tab,
            )
            for window in self.from_windows
            for ae_tab in window.ae_window.tabs()
        ]


class ChromeTabsFilter(TypedDict, total=False):
    url: str
    url__eq: str
    url__ne: str
    url__in: Collection[str]
    url__contains: str
    url__startswith: str
    url__endswith: str

    title: str
    title__eq: str
    title__ne: str
    title__in: Collection[str]
    title__contains: str
    title__startswith: str
    title__endswith: str

    loading: bool
    loading__eq: bool
    loading__ne: bool

    id: str
    id__eq: str
    id__ne: str
    id__in: Collection[str]
    id__contains: str
    id__startswith: str
    id__endswith: str
