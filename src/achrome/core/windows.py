from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, NamedTuple, TypedDict

from pydantic import TypeAdapter

from achrome.core._internal.manager import BaseManager
from achrome.core._internal.models import ChromeModel
from achrome.core.tabs import Tab, TabsManager

if TYPE_CHECKING:
    from typing_extensions import NotRequired, Self, Unpack


class Bounds(NamedTuple):
    x: int
    y: int
    width: int
    height: int


@dataclass(slots=True)
class Window(ChromeModel):
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
    active_tab_id: str

    tabs: TabsManager = field(init=False)

    @property
    def active_tab(self) -> Tab:
        return self.tabs.get(id=self.active_tab_id)


class WindowsFilterCriteria(TypedDict):
    id: NotRequired[int]
    id__in: NotRequired[list[int]]
    name: NotRequired[str]
    name__in: NotRequired[list[str]]
    name__contains: NotRequired[str]
    bounds: NotRequired[Bounds]
    bounds__contains: NotRequired[int]
    index: NotRequired[int]
    index__in: NotRequired[list[int]]
    closeable: NotRequired[bool]
    minimizable: NotRequired[bool]
    minimized: NotRequired[bool]
    resizable: NotRequired[bool]
    visible: NotRequired[bool]
    zoomable: NotRequired[bool]
    zoomed: NotRequired[bool]
    mode: NotRequired[str]
    mode__contains: NotRequired[str]
    mode__in: NotRequired[list[str]]
    active_tab_index: NotRequired[int]
    active_tab_index__in: NotRequired[list[int]]
    presenting: NotRequired[bool]
    active_tab_id: NotRequired[str]
    active_tab_id__contains: NotRequired[str]
    active_tab_id__in: NotRequired[list[str]]


class WindowsManager(BaseManager[Window]):
    def _load_items(self) -> list[Window]:
        script = """
        use AppleScript version "2.8"
        use framework "Foundation"
        use scripting additions

        on integerOrZero(v)
            if v is missing value then
                return 0
            end if
            try
                return v as integer
            on error
                return 0
            end try
        end integerOrZero

        on boolOrFalse(v)
            if v is missing value then
                return false
            end if
            try
                return (v is true)
            on error
                return false
            end try
        end boolOrFalse

        on nsBool(v)
            return current application's NSNumber's numberWithBool:(my boolOrFalse(v))
        end nsBool

        on textOrEmpty(v)
            if v is missing value then
                return ""
            end if
            try
                return v as text
            on error
                return ""
            end try
        end textOrEmpty

        on boundsOrZero(rawBounds)
            if rawBounds is missing value then
                return {0, 0, 0, 0}
            end if
            try
                if (count of rawBounds) is not 4 then
                    return {0, 0, 0, 0}
                end if
                return {¬
                    my integerOrZero(item 1 of rawBounds), ¬
                    my integerOrZero(item 2 of rawBounds), ¬
                    my integerOrZero(item 3 of rawBounds), ¬
                    my integerOrZero(item 4 of rawBounds)}
            on error
                return {0, 0, 0, 0}
            end try
        end boundsOrZero

        set windowData to current application's NSMutableArray's array()

        tell application "Google Chrome"
            repeat with w in windows
                set windowRec to current application's NSMutableDictionary's dictionary()
                set rawId to missing value
                set rawBounds to missing value
                set rawName to missing value
                set rawMode to missing value
                set rawIndex to missing value
                set rawCloseable to missing value
                set rawMinimizable to missing value
                set rawMinimized to missing value
                set rawResizable to missing value
                set rawVisible to missing value
                set rawZoomable to missing value
                set rawZoomed to missing value
                set rawActiveTabIndex to missing value
                set rawPresenting to missing value
                set rawActiveTabId to missing value

                try
                    set rawId to id of w
                end try
                windowRec's setObject:(my integerOrZero(rawId)) forKey:"id"

                try
                    set rawName to name of w
                end try
                windowRec's setObject:(my textOrEmpty(rawName)) forKey:"name"

                try
                    set rawBounds to bounds of w
                end try
                windowRec's setObject:(my boundsOrZero(rawBounds)) forKey:"bounds"

                try
                    set rawIndex to index of w
                end try
                windowRec's setObject:(my integerOrZero(rawIndex)) forKey:"index"

                try
                    set rawCloseable to closeable of w
                end try
                windowRec's setObject:(my nsBool(rawCloseable)) forKey:"closeable"

                try
                    set rawMinimizable to minimizable of w
                end try
                windowRec's setObject:(my nsBool(rawMinimizable)) forKey:"minimizable"

                try
                    set rawMinimized to minimized of w
                end try
                windowRec's setObject:(my nsBool(rawMinimized)) forKey:"minimized"

                try
                    set rawResizable to resizable of w
                end try
                windowRec's setObject:(my nsBool(rawResizable)) forKey:"resizable"

                try
                    set rawVisible to visible of w
                end try
                windowRec's setObject:(my nsBool(rawVisible)) forKey:"visible"

                try
                    set rawZoomable to zoomable of w
                end try
                windowRec's setObject:(my nsBool(rawZoomable)) forKey:"zoomable"

                try
                    set rawZoomed to zoomed of w
                end try
                windowRec's setObject:(my nsBool(rawZoomed)) forKey:"zoomed"

                try
                    set rawMode to mode of w
                end try
                windowRec's setObject:(my textOrEmpty(rawMode)) forKey:"mode"

                try
                    set rawActiveTabIndex to active tab index of w
                end try
                windowRec's setObject:(my integerOrZero(rawActiveTabIndex)) forKey:"active_tab_index"

                try
                    set rawPresenting to presenting of w
                end try
                windowRec's setObject:(my nsBool(rawPresenting)) forKey:"presenting"

                try
                    set rawActiveTabId to id of active tab of w
                end try
                windowRec's setObject:(my textOrEmpty(rawActiveTabId)) forKey:"active_tab_id"

                windowData's addObject:windowRec
            end repeat
        end tell

        set {jsonData, jsonError} to current application's NSJSONSerialization's ¬
            dataWithJSONObject:windowData options:0 |error|:(reference)

        if jsonData is missing value then
            return "JSON serialization failed: " & ((jsonError's localizedDescription()) as text)
        end if

        set jsonString to (current application's NSString's alloc()'s ¬
            initWithData:jsonData encoding:(current application's NSUTF8StringEncoding)) as text

        return jsonString

        """

        result = self._context.runner.run(script)
        windows = TypeAdapter(list[Window]).validate_json(result)

        for window in windows:
            window.tabs = TabsManager(_context=self._context, _window_id=window.id)
            window.set_context(self._context)

        return windows

    if TYPE_CHECKING:

        def filter(self, **criteria: Unpack[WindowsFilterCriteria]) -> Self: ...  # type: ignore[override]
        def get(self, **criteria: Unpack[WindowsFilterCriteria]) -> Window: ...  # type: ignore[override]
