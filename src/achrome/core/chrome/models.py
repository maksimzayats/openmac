from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

JsonValue: TypeAlias = (  # noqa: UP040
    str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
)


@dataclass(frozen=True, slots=True)
class ChromeApplicationInfo:
    """Information about the Chrome application."""

    name: str
    version: str
    frontmost: bool


@dataclass(frozen=True, slots=True)
class WindowBounds:
    """Window geometry in screen coordinates."""

    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        """Return computed window width."""
        return self.right - self.left

    @property
    def height(self) -> int:
        """Return computed window height."""
        return self.bottom - self.top


@dataclass(frozen=True, slots=True)
class ChromeWindow:
    """Represents a Chrome window."""

    id: str
    index: int
    name: str
    given_name: str
    bounds: WindowBounds
    closeable: bool
    minimizable: bool
    minimized: bool
    resizable: bool
    visible: bool
    zoomable: bool
    zoomed: bool
    mode: str
    active_tab_index: int
    active_tab_id: str
    tab_count: int


@dataclass(frozen=True, slots=True)
class ChromeTab:
    """Represents a Chrome tab."""

    id: str
    window_id: str
    index: int
    title: str
    url: str
    loading: bool
    window_name: str
    is_active: bool

    @property
    def composite_id(self) -> str:
        """Return chrome-cli style tab identifier."""
        return f"{self.window_id}:{self.id}"


@dataclass(frozen=True, slots=True)
class ChromeBookmarkItem:
    """Bookmark URL item."""

    id: str
    title: str
    url: str
    index: int


@dataclass(frozen=True, slots=True)
class ChromeBookmarkFolder:
    """Bookmark folder node."""

    id: str
    title: str
    index: int
    folders: list[ChromeBookmarkFolder] = field(default_factory=list)
    items: list[ChromeBookmarkItem] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ChromeBookmarks:
    """Top-level bookmark roots."""

    bookmarks_bar: ChromeBookmarkFolder
    other_bookmarks: ChromeBookmarkFolder


@dataclass(frozen=True, slots=True)
class TabTarget:
    """Tab selector supporting composite ids."""

    tab_id: str
    window_id: str | None = None

    @classmethod
    def parse(cls, value: str) -> TabTarget:
        """Parse tab target from `tab` or `window:tab` format."""
        normalized = value.strip()
        if not normalized:
            msg = "Tab target cannot be empty."
            raise ValueError(msg)
        if ":" not in normalized:
            return cls(tab_id=normalized, window_id=None)

        window_id, tab_id = normalized.split(":", 1)
        if not window_id or not tab_id:
            msg = f"Invalid tab target format: {value!r}"
            raise ValueError(msg)
        return cls(tab_id=tab_id, window_id=window_id)

    def to_cli(self) -> str:
        """Return chrome-cli compatible tab target."""
        if self.window_id is None:
            return self.tab_id
        return f"{self.window_id}:{self.tab_id}"


@dataclass(frozen=True, slots=True)
class WindowTarget:
    """Window selector."""

    window_id: str
