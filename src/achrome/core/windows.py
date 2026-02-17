from __future__ import annotations

from dataclasses import dataclass, field
from textwrap import dedent
from typing import TYPE_CHECKING, Literal, NamedTuple, TypedDict

from pydantic import TypeAdapter

from achrome.core._internal.manager import BaseManager
from achrome.core._internal.models import ChromeModel
from achrome.core._internal.tab_commands import NOT_FOUND_SENTINEL, build_void_tab_command_script
from achrome.core._internal.window_commands import build_void_window_command_script
from achrome.core.exceptions import DoesNotExistError
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
    active_tab_id: int

    tabs: TabsManager = field(init=False)

    @property
    def active_tab(self) -> Tab:
        return self.tabs.get(id=self.active_tab_id)

    def close(self) -> None:
        self._run_window_command("close", "close targetWindow")

    def activate(self) -> None:
        self._run_window_command(
            "activate",
            """
set index of targetWindow to 1
activate
""",
        )

    def set_bounds(self, bounds: Bounds) -> None:
        self._run_window_command(
            "set bounds",
            f"set bounds of targetWindow to {{{bounds.x}, {bounds.y}, {bounds.width}, {bounds.height}}}",
        )

    def minimize(self) -> None:
        self._run_window_command("minimize", "set minimized of targetWindow to true")

    def unminimize(self) -> None:
        self._run_window_command("unminimize", "set minimized of targetWindow to false")

    def show(self) -> None:
        self._run_window_command("show", "set visible of targetWindow to true")

    def hide(self) -> None:
        self._run_window_command("hide", "set visible of targetWindow to false")

    def zoom(self) -> None:
        self._run_window_command("zoom", "set zoomed of targetWindow to true")

    def unzoom(self) -> None:
        self._run_window_command("unzoom", "set zoomed of targetWindow to false")

    def enter_presentation_mode(self) -> None:
        self._run_window_command(
            "enter presentation mode",
            "enter presentation mode targetWindow",
        )

    def exit_presentation_mode(self) -> None:
        self._run_window_command(
            "exit presentation mode",
            "exit presentation mode targetWindow",
        )

    def activate_tab_index(self, tab_index: int) -> None:
        script = build_void_window_command_script(
            self.id,
            command_body=f"""
set active tab index of targetWindow to {tab_index}
activate
""",
        )
        result = self._context.runner.run(script)
        if result == NOT_FOUND_SENTINEL:
            raise DoesNotExistError(
                f"Cannot activate tab index={tab_index} in window id={self.id}: not found.",
            )

    def activate_tab(self, tab_id: int) -> None:
        script = build_void_tab_command_script(
            self.id,
            tab_id,
            command_body="""
set active tab index of targetWindow to tabIndex
activate
""",
        )
        result = self._context.runner.run(script)
        if result == NOT_FOUND_SENTINEL:
            raise DoesNotExistError(
                f"Cannot activate tab id={tab_id} in window id={self.id}: not found.",
            )

    def _run_window_command(self, action: str, command_body: str) -> None:
        script = build_void_window_command_script(self.id, command_body=command_body)
        result = self._context.runner.run(script)
        if result == NOT_FOUND_SENTINEL:
            raise DoesNotExistError(f"Cannot {action} window id={self.id}: not found.")


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
    active_tab_id: NotRequired[int]
    active_tab_id__in: NotRequired[list[int]]


class WindowsManager(BaseManager[Window]):
    @property
    def front(self) -> Window:
        return self.get(index=1)

    def create(self, *, mode: Literal["normal", "incognito"] = "normal") -> Window:
        create_window_command = "set targetWindow to make new window"
        if mode == "incognito":
            create_window_command = (
                'set targetWindow to make new window with properties {mode:"incognito"}'
            )

        script = dedent(
            f"""
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
                    return {{0, 0, 0, 0}}
                end if
                try
                    if (count of rawBounds) is not 4 then
                        return {{0, 0, 0, 0}}
                    end if
                    return {{¬
                        my integerOrZero(item 1 of rawBounds), ¬
                        my integerOrZero(item 2 of rawBounds), ¬
                        my integerOrZero(item 3 of rawBounds), ¬
                        my integerOrZero(item 4 of rawBounds)}}
                on error
                    return {{0, 0, 0, 0}}
                end try
            end boundsOrZero

            tell application "Google Chrome"
                {create_window_command}

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
                    set rawId to id of targetWindow
                end try
                windowRec's setObject:(my integerOrZero(rawId)) forKey:"id"

                try
                    set rawName to name of targetWindow
                end try
                windowRec's setObject:(my textOrEmpty(rawName)) forKey:"name"

                try
                    set rawBounds to bounds of targetWindow
                end try
                windowRec's setObject:(my boundsOrZero(rawBounds)) forKey:"bounds"

                try
                    set rawIndex to index of targetWindow
                end try
                windowRec's setObject:(my integerOrZero(rawIndex)) forKey:"index"

                try
                    set rawCloseable to closeable of targetWindow
                end try
                windowRec's setObject:(my nsBool(rawCloseable)) forKey:"closeable"

                try
                    set rawMinimizable to minimizable of targetWindow
                end try
                windowRec's setObject:(my nsBool(rawMinimizable)) forKey:"minimizable"

                try
                    set rawMinimized to minimized of targetWindow
                end try
                windowRec's setObject:(my nsBool(rawMinimized)) forKey:"minimized"

                try
                    set rawResizable to resizable of targetWindow
                end try
                windowRec's setObject:(my nsBool(rawResizable)) forKey:"resizable"

                try
                    set rawVisible to visible of targetWindow
                end try
                windowRec's setObject:(my nsBool(rawVisible)) forKey:"visible"

                try
                    set rawZoomable to zoomable of targetWindow
                end try
                windowRec's setObject:(my nsBool(rawZoomable)) forKey:"zoomable"

                try
                    set rawZoomed to zoomed of targetWindow
                end try
                windowRec's setObject:(my nsBool(rawZoomed)) forKey:"zoomed"

                try
                    set rawMode to mode of targetWindow
                end try
                windowRec's setObject:(my textOrEmpty(rawMode)) forKey:"mode"

                try
                    set rawActiveTabIndex to active tab index of targetWindow
                end try
                windowRec's setObject:(my integerOrZero(rawActiveTabIndex)) forKey:"active_tab_index"

                try
                    set rawPresenting to presenting of targetWindow
                end try
                windowRec's setObject:(my nsBool(rawPresenting)) forKey:"presenting"

                try
                    set rawActiveTabId to id of active tab of targetWindow
                end try
                windowRec's setObject:(my integerOrZero(rawActiveTabId)) forKey:"active_tab_id"

                set {{jsonData, jsonError}} to current application's NSJSONSerialization's ¬
                    dataWithJSONObject:windowRec options:0 |error|:(reference)

                if jsonData is missing value then
                    return "JSON serialization failed: " & ((jsonError's localizedDescription()) as text)
                end if

                set jsonString to (current application's NSString's alloc()'s ¬
                    initWithData:jsonData encoding:(current application's NSUTF8StringEncoding)) as text

                return jsonString
            end tell
            """,
        ).strip()

        result = self._context.runner.run(script)
        window = TypeAdapter(Window).validate_json(result)
        window.tabs = TabsManager(_context=self._context, _window_id=window.id)
        window.set_context(self._context)
        return window

    def _load_items(self) -> list[Window]:
        script = dedent(
            """
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
                    windowRec's setObject:(my integerOrZero(rawActiveTabId)) forKey:"active_tab_id"

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
            """,
        ).strip()

        result = self._context.runner.run(script)
        windows = TypeAdapter(list[Window]).validate_json(result)

        for window in windows:
            window.tabs = TabsManager(_context=self._context, _window_id=window.id)
            window.set_context(self._context)

        return windows

    if TYPE_CHECKING:

        def filter(self, **criteria: Unpack[WindowsFilterCriteria]) -> Self: ...  # type: ignore[override]
        def get(self, **criteria: Unpack[WindowsFilterCriteria]) -> Window: ...  # type: ignore[override]
