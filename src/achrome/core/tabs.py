from __future__ import annotations

import base64
import time
from dataclasses import dataclass, field
from textwrap import dedent, indent
from typing import TYPE_CHECKING, TypedDict, TypeVar, overload

from pydantic import TypeAdapter

from achrome.core._internal.manager import BaseManager
from achrome.core._internal.models import ChromeModel
from achrome.core._internal.tab_commands import (
    EXECUTE_MISSING_RESULT_SENTINEL,
    NOT_FOUND_SENTINEL,
    build_execute_script,
    build_tab_info_script,
    build_tabs_info_list_script,
    build_void_tab_command_script,
)
from achrome.core.exceptions import DoesNotExistError
from achrome.core.source import Snapshot

if TYPE_CHECKING:
    from typing_extensions import NotRequired, Self, Unpack


T = TypeVar("T")


@dataclass(slots=True, frozen=True)
class _TabInfo:
    title: str
    url: str
    loading: bool
    is_active: bool


@dataclass(slots=True, frozen=True)
class _TabListInfo:
    id: int
    title: str
    url: str
    loading: bool
    is_active: bool


@dataclass(slots=True, kw_only=True)
class Tab(ChromeModel):
    id: int
    window_id: int
    _info: _TabInfo | None = field(default=None, repr=False, compare=False)

    def _require_info(self) -> _TabInfo:
        if self._info is None:
            raise RuntimeError(
                f"Tab id={self.id} in window id={self.window_id} state is not hydrated. "
                "Call `tab.refresh()` before accessing properties.",
            )
        return self._info

    def refresh(self) -> Self:
        script = build_tab_info_script(self.window_id, self.id)
        result = self._context.runner.run(script)
        self._raise_if_not_found(result, action="read")
        self._info = TypeAdapter(_TabInfo).validate_json(result)
        return self

    @property
    def title(self) -> str:
        return self._require_info().title

    @property
    def url(self) -> str:
        return self._require_info().url

    @property
    def loading(self) -> bool:
        return self._require_info().loading

    @property
    def is_active(self) -> bool:
        return self._require_info().is_active

    @property
    def source(self) -> str:
        source = self.execute("document.documentElement.outerHTML")
        if source is None:
            raise RuntimeError(
                f"Cannot read source for tab id={self.id} in window id={self.window_id}: "
                "JavaScript returned no value.",
            )
        return source

    @property
    def snapshot(self) -> Snapshot:
        return Snapshot.from_source(self.source)

    def close(self) -> None:
        self._run_tab_command(action="close", command_body="close t")

    def reload(self) -> None:
        self._run_tab_command(action="reload", command_body="reload t")
        self.refresh()

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

    @overload
    def execute(self, javascript: str, *, return_type: type[T]) -> T: ...

    @overload
    def execute(self, javascript: str, *, return_type: None = None) -> str | None: ...

    def execute(self, javascript: str, *, return_type: type[T] | None = None) -> T | str | None:
        script = build_execute_script(self.window_id, self.id, javascript)
        result = self._context.runner.run(script)
        self._raise_if_not_found(result, action="execute JavaScript in")
        if result == EXECUTE_MISSING_RESULT_SENTINEL:
            if return_type is not None:
                raise RuntimeError(
                    f"Expected a return value from executing JavaScript in tab id={self.id} "
                    f"in window id={self.window_id}, but got none.",
                )

            return None

        if return_type is not None:
            try:
                return TypeAdapter(return_type).validate_json(result)
            except Exception as error:
                raise RuntimeError(
                    f"Failed to parse JavaScript execution result as {return_type}: {error}",
                ) from error

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

    def wait_to_load(self, timeout: float | None = None) -> Self:
        start_time = time.monotonic()
        self.refresh()
        while self.loading:
            if timeout is not None and (time.monotonic() - start_time) > timeout:
                raise TimeoutError(
                    f"Timed out waiting for tab id={self.id} in window id={self.window_id} to load.",
                )

            time.sleep(0.1)
            self.refresh()

        return self


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


class _GlobalTabOpenResult(TypedDict):
    id: int
    window_id: int


class _WindowTabOpenResult(TypedDict):
    id: int


@dataclass(kw_only=True)
class TabsManager(BaseManager[Tab]):
    _window_id: int | None = None
    """A window id to which the tabs belong."""

    def __post_init__(self) -> None:
        if self._items is None and self._window_id is None:
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

        if self._window_id is None:
            open_result_global = TypeAdapter(_GlobalTabOpenResult).validate_json(result)
            tab = Tab(
                id=open_result_global["id"],
                window_id=open_result_global["window_id"],
            )
        else:
            window_id = self._window_id
            open_result_window = TypeAdapter(_WindowTabOpenResult).validate_json(result)
            tab = Tab(id=open_result_window["id"], window_id=window_id)
        tab.set_context(self._context)
        return tab.refresh()

    def _load_items(self) -> list[Tab]:
        if self._window_id is None:
            raise RuntimeError("Cannot load tabs without a window id.")

        window_id = self._window_id
        script = build_tabs_info_list_script(window_id)
        result = self._context.runner.run(script)
        tab_infos = TypeAdapter(list[_TabListInfo]).validate_json(result)
        tabs = [
            Tab(
                id=tab_info.id,
                window_id=window_id,
                _info=_TabInfo(
                    title=tab_info.title,
                    url=tab_info.url,
                    loading=tab_info.loading,
                    is_active=tab_info.is_active,
                ),
            )
            for tab_info in tab_infos
        ]

        for tab in tabs:
            tab.set_context(self._context)

        return tabs

    if TYPE_CHECKING:

        def get(self, **criteria: Unpack[TabsFilterCriteria]) -> Tab: ...  # type: ignore[override]
        def filter(self, **criteria: Unpack[TabsFilterCriteria]) -> TabsManager: ...  # type: ignore[override]
