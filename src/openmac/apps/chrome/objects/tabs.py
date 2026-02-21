from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

from appscript import GenericReference, Keyword, k

from openmac.apps._internal.base import BaseManager, BaseObject
from openmac.apps.system_events.helpers import preserve_focus as preserve_focus_context_manager

if TYPE_CHECKING:
    from collections.abc import Collection

    from typing_extensions import Unpack


@dataclass(slots=True)
class ChromeTab(BaseObject):
    _from_ae_window: GenericReference

    # region Properties

    @property
    def url(self) -> str:
        return self._ae_object.URL()

    @property
    def title(self) -> str:
        return self._ae_object.title()

    @property
    def loading(self) -> bool:
        return self._ae_object.loading()

    @property
    def id(self) -> str:
        return self._ae_object.id()

    @property
    def properties(self) -> ChromeTabProperties:
        ae_properties = self._ae_object.properties()
        return ChromeTabProperties(
            url=ae_properties[Keyword("URL")],
            title=ae_properties[Keyword("title")],
            loading=ae_properties[Keyword("loading")],
            id=ae_properties[Keyword("id")],
        )

    # endregion Properties

    # region Actions

    def reload(self) -> None:
        self._ae_object.reload()

    def close(self) -> None:
        self._ae_object.close()

    def go_back(self) -> None:
        self._ae_object.go_back()

    def go_forward(self) -> None:
        self._ae_object.go_forward()

    def duplicate(self) -> ChromeTab:
        ae_tab = self._from_ae_window.tabs.end.make(
            new=k.tab,
            with_properties={
                Keyword("URL"): self.url,
            },
        )

        return ChromeTab(
            _ae_application=self._ae_application,
            _ae_object=ae_tab,
            _from_ae_window=self._from_ae_window,
        )

    def execute(self, javascript: str) -> str:
        return self._ae_object.execute(javascript=javascript)

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
class ChromeTabsManager(BaseManager[ChromeTab]):
    _from_ae_window: GenericReference
    """ChromeWindow object from which this manager was created. Needed to create new tabs with the correct parent window."""

    if TYPE_CHECKING:

        def get(self, **filters: Unpack[ChromeTabsFilter]) -> ChromeTab: ...  # type: ignore[override]
        def filter(self, **filters: Unpack[ChromeTabsFilter]) -> BaseManager[ChromeTab]: ...  # type: ignore[override]
        def exclude(self, **filters: Unpack[ChromeTabsFilter]) -> BaseManager[ChromeTab]: ...  # type: ignore[override]

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
            _ae_application=self._ae_application,
            _ae_object=ae_tab,
            _from_ae_window=self._from_ae_window,
        )

        if wait_until_loaded:
            tab.wait_until_loaded()

        return tab

    def _make_ae_tab(self, url: str) -> GenericReference:
        return self._from_ae_window.tabs.end.make(
            new=k.tab,
            with_properties={
                Keyword("URL"): url,
            },
        )


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
