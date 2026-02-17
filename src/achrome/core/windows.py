from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from typing import NotRequired


class Windows:
    def __init__(self, windows: list[Window]) -> None:
        self._windows = windows

    def __iter__(self) -> Iterator[Window]:
        return iter(self._windows)


@dataclass(slots=True)
class Window:
    id: str
    name: str


class WindowsFilterCriteria(TypedDict):
    id: NotRequired[str]
    id__in: NotRequired[list[str]]
    name: NotRequired[str]
    name__in: NotRequired[list[str]]
    name__contains: NotRequired[str]
