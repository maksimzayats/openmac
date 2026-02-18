from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias, TypedDict

from typing_extensions import NotRequired

from openmac._internal.manager import Manager
from openmac._internal.models import MacModel

Bounds: TypeAlias = tuple[int, int, int, int]


class Application(MacModel):
    name: str
    frontmost: bool
    version: str

    windows: Manager[Window]


class Window(MacModel):
    id: int

    name: str
    bounds: Bounds
    index: int
    closeable: bool
    minimizable: bool
    minimized: bool
    resizable: bool
    visible: bool
    zoomable: bool
    zoomed: bool
    mode: str
    active_tab_index: int
    presenting: bool
    active_tab_id: int

    @property
    def tabs(self) -> TabsManager:
        return TabsManager(_context=self._context, _window_id=self.id)


class Tab(MacModel):
    id: int
    window_id: int

    title: str
    url: str
    loading: bool
    is_active: bool


class TabsFilterCriteria(TypedDict):
    id: NotRequired[int]
    id__in: NotRequired[list[int]]
    title: NotRequired[str]
    title__in: NotRequired[list[str]]
    title__contains: NotRequired[str]
    url: NotRequired[str]
    url__in: NotRequired[list[str]]
    url__contains: NotRequired[str]
    loading: NotRequired[bool]
    loading__in: NotRequired[list[bool]]
    is_active: NotRequired[bool]


class TabsManager(Manager[Tab]):
    if TYPE_CHECKING:

        def get(self, **criteria: Unpack[TabsFilterCriteria]) -> Tab: ...  # type: ignore[override]
        def filter(self, **criteria: Unpack[TabsFilterCriteria]) -> TabsManager: ...  # type: ignore[override]
