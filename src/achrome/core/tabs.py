from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

from achrome.core._internal.manager import BaseManager

if TYPE_CHECKING:
    from typing_extensions import NotRequired


@dataclass(slots=True, kw_only=True, frozen=True)
class Tab:
    id: str
    window_id: str
    name: str
    url: str
    loading: bool

    @property
    def source(self) -> str:
        return "<html>...</html>"  # Placeholder for the actual page source

    def execute(self, javascript: str) -> str:
        # Placeholder for executing JavaScript in the tab and returning the result
        _ = javascript, self  # Use the JavaScript code to execute in the tab
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


@dataclass(kw_only=True)
class TabsManager(BaseManager[Tab]):
    _window_id: str | None = None
    """A window id to which the tabs belong."""

    def _load_items(self) -> list[Tab]:
        if self._window_id is None:
            raise RuntimeError("Cannot load tabs without a window id.")

        return [
            Tab(
                id="tab-1",
                window_id=self._window_id or "window-1",
                name="Tab 1",
                url="https://example.com",
                loading=False,
            ),
            Tab(
                id="tab-2",
                window_id=self._window_id or "window-1",
                name="Tab 2",
                url="https://example.org",
                loading=True,
            ),
            Tab(
                id="tab-3",
                window_id=self._window_id or "window-2",
                name="Tab 3",
                url="https://example.net",
                loading=False,
            ),
        ]
