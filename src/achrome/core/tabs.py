from __future__ import annotations

import base64
from dataclasses import dataclass
from textwrap import dedent, indent
from typing import TYPE_CHECKING, TypedDict

from pydantic import TypeAdapter

from achrome.core._internal.manager import BaseManager
from achrome.core._internal.models import ChromeModel
from achrome.core._internal.tab_commands import (
    NOT_FOUND_SENTINEL,
    build_execute_script,
    build_void_tab_command_script,
)
from achrome.core.exceptions import DoesNotExistError

if TYPE_CHECKING:
    from typing_extensions import NotRequired, Unpack


@dataclass(slots=True, kw_only=True)
class Tab(ChromeModel):
    id: int
    window_id: int
    title: str
    url: str
    loading: bool
    is_active: bool

    @property
    def source(self) -> str:
        return self.execute("document.documentElement.outerHTML")

    def close(self) -> None:
        self._run_tab_command(action="close", command_body="close t")

    def reload(self) -> None:
        self._run_tab_command(action="reload", command_body="reload t")

    def back(self) -> None:
        self._run_tab_command(action="go back", command_body="go back t")

    def forward(self) -> None:
        self._run_tab_command(action="go forward", command_body="go forward t")

    def activate(self) -> None:
        self._run_tab_command(
            action="activate",
            command_body="""
set active tab index of targetWindow to tabIndex
activate
""",
        )

    def enter_presentation_mode(self) -> None:
        self._run_window_command(
            action="enter presentation mode",
            command_body="enter presentation mode targetWindow",
        )

    def exit_presentation_mode(self) -> None:
        self._run_window_command(
            action="exit presentation mode",
            command_body="exit presentation mode targetWindow",
        )

    def execute(self, javascript: str) -> str:
        script = build_execute_script(self.window_id, self.id, javascript)
        result = self._context.runner.run(script)
        self._raise_if_not_found(result, action="execute JavaScript in")
        return result

    def _run_tab_command(self, *, action: str, command_body: str) -> None:
        script = build_void_tab_command_script(self.window_id, self.id, command_body=command_body)
        result = self._context.runner.run(script)
        self._raise_if_not_found(result, action=action)

    def _run_window_command(self, *, action: str, command_body: str) -> None:
        command_lines = indent(dedent(command_body).strip(), "    ")
        script = dedent(
            f"""
            use AppleScript version "2.8"
            use scripting additions

            tell application "Google Chrome"
                set targetWindowId to {self.window_id}
                set targetWindow to missing value

                repeat with w in windows
                    if ((id of w) as integer) is targetWindowId then
                        set targetWindow to w
                        exit repeat
                    end if
                end repeat

                if targetWindow is missing value then
                    return "{NOT_FOUND_SENTINEL}"
                end if

            __ACHROME_COMMAND_BODY__
                return "ok"
            end tell
            """,
        ).strip()
        script = script.replace("__ACHROME_COMMAND_BODY__", command_lines)
        result = self._context.runner.run(script)
        self._raise_if_not_found(result, action=action)

    def _raise_if_not_found(self, result: str, *, action: str) -> None:
        if result == NOT_FOUND_SENTINEL:
            raise DoesNotExistError(
                f"Cannot {action} tab id={self.id} in window id={self.window_id}: not found.",
            )


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

    def open(self, url: str) -> Tab:
        """Open URL in a new window globally, or a tab in the bound window, without activation.

        Raises:
            DoesNotExistError: If the bound window does not exist.

        """
        url_b64 = base64.b64encode(url.encode("utf-8")).decode("ascii")

        if self._window_id is None:
            script = dedent(
                f"""
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

                set urlBase64 to "{url_b64}"
                set urlData to current application's NSData's alloc()'s ¬
                    initWithBase64EncodedString:urlBase64 options:0
                if urlData is missing value then
                    set urlText to ""
                else
                    set urlText to (current application's NSString's alloc()'s ¬
                        initWithData:urlData encoding:(current application's NSUTF8StringEncoding)) as text
                end if

                tell application "Google Chrome"
                    set targetWindow to make new window
                    set t to active tab of targetWindow
                    set URL of t to urlText

                    set tabRec to current application's NSMutableDictionary's dictionary()
                    tabRec's setObject:((id of t) as integer) forKey:"id"
                    tabRec's setObject:((id of targetWindow) as integer) forKey:"window_id"
                    tabRec's setObject:(my textOrEmpty(title of t)) forKey:"title"
                    tabRec's setObject:(my textOrEmpty(URL of t)) forKey:"url"
                    tabRec's setObject:(my nsBool(loading of t)) forKey:"loading"
                    tabRec's setObject:(my nsBool(true)) forKey:"is_active"

                    set {{jsonData, jsonError}} to current application's NSJSONSerialization's ¬
                        dataWithJSONObject:tabRec options:0 |error|:(reference)

                    if jsonData is missing value then
                        return "JSON serialization failed: " & ((jsonError's localizedDescription()) as text)
                    end if

                    set jsonString to (current application's NSString's alloc()'s ¬
                        initWithData:jsonData encoding:(current application's NSUTF8StringEncoding)) as text

                    return jsonString
                end tell
                """,
            ).strip()
        else:
            script = dedent(
                f"""
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
                set urlBase64 to "{url_b64}"
                set urlData to current application's NSData's alloc()'s ¬
                    initWithBase64EncodedString:urlBase64 options:0
                if urlData is missing value then
                    set urlText to ""
                else
                    set urlText to (current application's NSString's alloc()'s ¬
                        initWithData:urlData encoding:(current application's NSUTF8StringEncoding)) as text
                end if

                tell application "Google Chrome"
                    set targetWindow to missing value

                    repeat with w in windows
                        if ((id of w) as integer) is targetWindowId then
                            set targetWindow to w
                            exit repeat
                        end if
                    end repeat

                    if targetWindow is missing value then
                        return "{NOT_FOUND_SENTINEL}"
                    end if

                    set newTab to make new tab at end of tabs of targetWindow with properties {{URL:urlText}}
                    set active tab index of targetWindow to (count of tabs of targetWindow)

                    set tabRec to current application's NSMutableDictionary's dictionary()
                    tabRec's setObject:((id of newTab) as integer) forKey:"id"
                    tabRec's setObject:targetWindowId forKey:"window_id"
                    tabRec's setObject:(my textOrEmpty(title of newTab)) forKey:"title"
                    tabRec's setObject:(my textOrEmpty(URL of newTab)) forKey:"url"
                    tabRec's setObject:(my nsBool(loading of newTab)) forKey:"loading"
                    tabRec's setObject:(my nsBool(true)) forKey:"is_active"

                    set {{jsonData, jsonError}} to current application's NSJSONSerialization's ¬
                        dataWithJSONObject:tabRec options:0 |error|:(reference)

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
        if result == NOT_FOUND_SENTINEL:
            raise DoesNotExistError(f"Cannot open tab in window id={self._window_id}: not found.")

        tab = TypeAdapter(Tab).validate_json(result)
        tab.set_context(self._context)
        return tab

    def _load_items(self) -> list[Tab]:
        if self._window_id is None:
            raise RuntimeError("Cannot load tabs without a window id.")

        script = dedent(
            f"""
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

                    tabRec's setObject:((id of t) as integer) forKey:"id"
                    tabRec's setObject:targetWindowId forKey:"window_id"
                    tabRec's setObject:(my textOrEmpty(title of t)) forKey:"title"
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
            """,
        ).strip()

        result = self._context.runner.run(script)
        tabs = TypeAdapter(list[Tab]).validate_json(result)

        for tab in tabs:
            tab.set_context(self._context)

        return tabs

    if TYPE_CHECKING:

        def get(self, **criteria: Unpack[TabsFilterCriteria]) -> Tab: ...  # type: ignore[override]
        def filter(self, **criteria: Unpack[TabsFilterCriteria]) -> TabsManager: ...  # type: ignore[override]
