from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

from achrome.core._internal.context import context
from achrome.core._internal.manager import BaseManager
from achrome.core.tabs import TabsManager

if TYPE_CHECKING:
    from typing_extensions import NotRequired, Self, Unpack


@dataclass(slots=True)
class Window:
    id: str
    name: str
    tabs: TabsManager


class WindowsFilterCriteria(TypedDict):
    id: NotRequired[str]
    id__in: NotRequired[list[str]]
    name: NotRequired[str]
    name__in: NotRequired[list[str]]
    name__contains: NotRequired[str]


class WindowsManager(BaseManager[Window]):
    def _load_items(self) -> list[Window]:
        _ = context.chrome_api.get_windows()
        return [
            Window(
                id="window-1",
                name="Window 1",
                tabs=TabsManager(_window_id="window-1"),
            ),
            Window(id="window-2", name="Window 2", tabs=TabsManager(_window_id="window-2")),
        ]

    if TYPE_CHECKING:

        def filter(self, **criteria: Unpack[WindowsFilterCriteria]) -> Self: ...  # type: ignore[override]
