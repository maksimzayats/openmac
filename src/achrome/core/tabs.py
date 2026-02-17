from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypedDict

from pydantic import TypeAdapter

from achrome.core._internal.context import Context
from achrome.core._internal.manager import BaseManager

if TYPE_CHECKING:
    from typing_extensions import NotRequired, Unpack


@dataclass(slots=True, kw_only=True)
class Tab:
    id: str
    window_id: int
    name: str
    url: str
    loading: bool
    is_active: bool = False

    _context: Context = field(init=False)

    @property
    def source(self) -> str:
        return "<html>...</html>"  # Placeholder for the actual page source

    def execute(self, javascript: str) -> str:
        # Placeholder for executing JavaScript in the tab and returning the result
        _ = javascript, self  # Use the JavaScript code to execute in the tab
        return "result of executing JavaScript"

    def close(self) -> None: ...

    def reload(self) -> None: ...

    def back(self) -> None: ...

    def forward(self) -> None: ...

    def activate(self) -> None: ...

    def enter_presentation_mode(self) -> None: ...

    def exit_presentation_mode(self) -> None: ...


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
    is_active: NotRequired[bool]


@dataclass(kw_only=True)
class TabsManager(BaseManager[Tab]):
    _window_id: int | None = None
    """A window id to which the tabs belong."""

    def __post_init__(self) -> None:
        if not self._items and self._window_id is None:
            raise ValueError("TabsManager requires either _items or _window_id to be provided.")

        if self._window_id is not None:
            self._default_filters = {"window_id": self._window_id}

    @property
    def active(self) -> Tab:
        return self.get(is_active=True)

    def open(
        self,
        url: str,
        *,
        new_window: bool = False,
        incognito: bool = False,
    ) -> Tab:
        raise NotImplementedError

    def _load_items(self) -> list[Tab]:
        if self._window_id is None:
            raise RuntimeError("Cannot load tabs without a window id.")

        script = f"""
        use AppleScript version "2.8"
        use framework "Foundation"
        use scripting additions

        on nsBool(v)
            return current application's NSNumber's numberWithBool:(v = true)
        end nsBool

        on textOrEmpty(v)
            if v is missing value then
                return ""
            end if
            return v as text
        end textOrEmpty

        set targetWindowId to {self._window_id}
        set tabData to current application's NSMutableArray's array()

        tell application "Google Chrome"
            set targetWindow to missing value

            repeat with w in windows
                if ((id of w) as integer) is targetWindowId then
                    set targetWindow to w
                    exit repeat
                end if
            end repeat

            if targetWindow is missing value then
                return "[]"
            end if

            set activeTabIndex to active tab index of targetWindow
            set tabCount to (count of tabs of targetWindow)

            repeat with tabIndex from 1 to tabCount
                set t to tab tabIndex of targetWindow
                set tabRec to current application's NSMutableDictionary's dictionary()

                tabRec's setObject:((id of t) as text) forKey:"id"
                tabRec's setObject:targetWindowId forKey:"window_id"
                tabRec's setObject:(my textOrEmpty(title of t)) forKey:"name"
                tabRec's setObject:(my textOrEmpty(URL of t)) forKey:"url"
                tabRec's setObject:(my nsBool(loading of t)) forKey:"loading"
                tabRec's setObject:(my nsBool(tabIndex is activeTabIndex)) forKey:"is_active"

                tabData's addObject:tabRec
            end repeat
        end tell

        set {{jsonData, jsonError}} to current application's NSJSONSerialization's ¬
            dataWithJSONObject:tabData options:0 |error|:(reference)

        if jsonData is missing value then
            return "JSON serialization failed: " & ((jsonError's localizedDescription()) as text)
        end if

        set jsonString to (current application's NSString's alloc()'s ¬
            initWithData:jsonData encoding:(current application's NSUTF8StringEncoding)) as text

        return jsonString
        """

        result = self._context.runner.run(script)
        adapter = TypeAdapter(list[Tab])
        tabs = adapter.validate_json(result)

        for tab in tabs:
            tab._context = self._context  # noqa: SLF001

        return tabs

    if TYPE_CHECKING:

        def get(self, **criteria: Unpack[TabsFilterCriteria]) -> Tab: ...  # type: ignore[override]
        def filter(self, **criteria: Unpack[TabsFilterCriteria]) -> TabsManager: ...  # type: ignore[override]
