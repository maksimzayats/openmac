from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator, TypedDict, Unpack

if TYPE_CHECKING:
    from typing import NotRequired


class Chrome:
    def __init__(self) -> None:
        self._chrome_api = None

    @property
    def tabs(self) -> Tabs:
        return Tabs(tabs=self._get_all_tabs())

    def _get_all_tabs(self) -> list[Tab]:
        _ = self._chrome_api  # Use the Chrome API to retrieve tabs

        # Placeholder implementation, replace with actual logic to retrieve tabs from Chrome
        return [
            Tab(id="1", name="Tab 1", url="https://example.com", loading=False),
            Tab(id="2", name="Tab 2", url="https://example.org", loading=True),
        ]


class Tabs:
    def __init__(self, tabs: list[Tab]) -> None:
        self._tabs = tabs

    def __iter__(self) -> Iterator[Tab]:
        return iter(self._tabs)

    def filter(
        self,
        **criteria: Unpack[TabsFilterCriteria],
    ) -> Tabs:
        """Filter tabs based on the provided criteria.

        If more than one filter is provided, the `OR` operator is applied between them.
        """

        filterer = TabsFilterer(criteria)
        filtered_tabs = filterer.filter(self._tabs)

        return Tabs(tabs=filtered_tabs)


@dataclass(slots=True, kw_only=True, frozen=True)
class Tab:
    id: str
    name: str
    url: str
    loading: bool

    @property
    def source(self) -> str:
        return "<html>...</html>"  # Placeholder for the actual page source

    def execute(self, javascript: str) -> str:
        # Placeholder for executing JavaScript in the tab and returning the result
        _ = javascript  # Use the JavaScript code to execute in the tab
        return "result of executing JavaScript"
    



class TabsFilterCriteria(TypedDict):
    id: NotRequired[str]
    id__in: NotRequired[list[str]]
    id__contains: NotRequired[str]
    name: NotRequired[str]
    name__in: NotRequired[list[str]]
    name__contains: NotRequired[str]
    url: NotRequired[str]
    url__in: NotRequired[list[str]]
    url__contains: NotRequired[str]
    loading: NotRequired[bool]
    loading__in: NotRequired[list[bool]]


class TabsFilterer:
    def __init__(self, criteria: TabsFilterCriteria) -> None:
        self._criteria = criteria

    def filter(self, tabs: list[Tab]) -> list[Tab]:
        return [tab for tab in tabs if self._matches_criteria(tab)]

    def _matches_criteria(self, tab: Tab) -> bool:  # noqa: C901, PLR0911
        if "id" in self._criteria and tab.id != self._criteria["id"]:
            return False

        if "id__in" in self._criteria and tab.id not in self._criteria["id__in"]:
            return False

        if "id__contains" in self._criteria and self._criteria["id__contains"] not in tab.id:
            return False

        if "name" in self._criteria and tab.name != self._criteria["name"]:
            return False

        if "name__in" in self._criteria and tab.name not in self._criteria["name__in"]:
            return False

        if "name__contains" in self._criteria and self._criteria["name__contains"] not in tab.name:
            return False

        if "url" in self._criteria and tab.url != self._criteria["url"]:
            return False

        if "url__in" in self._criteria and tab.url not in self._criteria["url__in"]:
            return False

        if "url__contains" in self._criteria and self._criteria["url__contains"] not in tab.url:
            return False

        if "loading" in self._criteria and tab.loading != self._criteria["loading"]:
            return False

        if "loading__in" in self._criteria and tab.loading not in self._criteria["loading__in"]:  # noqa: SIM103
            return False

        return True


def main() -> None:
    chrome = Chrome()
    tabs = chrome.tabs.filter(name__contains="Tab 1")
