from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import cast

from achrome.core.apple_script.executor import AppleScriptExecutorLike
from achrome.core.chrome.backend import ChromeAppleScriptBackend
from achrome.core.chrome.errors import AppleScriptDecodeError, ChromeError
from achrome.core.chrome.models import (
    ChromeApplicationInfo,
    ChromeBookmarkFolder,
    ChromeBookmarkItem,
    ChromeBookmarks,
    ChromeTab,
    ChromeWindow,
    JsonValue,
    TabTarget,
    WindowBounds,
    WindowTarget,
)

CHROME_BUNDLE_IDENTIFIER_ENV = "CHROME_BUNDLE_IDENTIFIER"
DEFAULT_CHROME_BUNDLE_IDENTIFIER = "com.google.Chrome"


def _bundle_identifier_from_env() -> str:
    return os.environ.get(CHROME_BUNDLE_IDENTIFIER_ENV, DEFAULT_CHROME_BUNDLE_IDENTIFIER)


@dataclass(kw_only=True, slots=True)
class ChromeAPI:
    """High-level API for controlling Chrome via AppleScript."""

    apple_script_executor: AppleScriptExecutorLike
    bundle_identifier: str = field(default_factory=_bundle_identifier_from_env)

    def application_info(self) -> ChromeApplicationInfo:
        """Return application metadata."""
        data = self._run("app_info")
        payload = _as_dict(value=data, context="app_info")
        return ChromeApplicationInfo(
            name=_as_str(value=payload.get("name"), field_name="name"),
            version=_as_str(value=payload.get("version"), field_name="version"),
            frontmost=_as_bool(value=payload.get("frontmost"), field_name="frontmost"),
        )

    def list_windows(self) -> list[ChromeWindow]:
        """List windows ordered by window index."""
        data = self._run("list_windows")
        payload = _as_list(value=data, context="list_windows")
        windows = [self._parse_window(item) for item in payload]
        return sorted(windows, key=lambda window: window.index)

    def list_tabs(self, *, window: WindowTarget | None = None) -> list[ChromeTab]:
        """List tabs ordered by window index then tab index."""
        args: tuple[str, ...] = ()
        if window is not None:
            args = (window.window_id,)
        data = self._run("list_tabs", *args)
        payload = _as_list(value=data, context="list_tabs")
        tabs = [self._parse_tab(item) for item in payload]
        if window is not None:
            return sorted(tabs, key=lambda tab: tab.index)
        window_order = {one_window.id: one_window.index for one_window in self.list_windows()}
        return sorted(
            tabs,
            key=lambda tab: (window_order.get(tab.window_id, 999_999), tab.index),
        )

    def active_tab(self) -> ChromeTab:
        """Return the active tab for the front window."""
        data = self._run("active_tab")
        return self._parse_tab(data)

    def tab(self, target: TabTarget | str) -> ChromeTab:
        """Resolve a tab by id or composite id."""
        resolved_target = self._tab_target(target=target)
        data = self._run("tab_info", resolved_target.to_cli())
        return self._parse_tab(data)

    def activate_tab(self, target: TabTarget | str, *, focus_window: bool = False) -> None:
        """Activate the target tab."""
        resolved_target = self._tab_target(target=target)
        self._run("activate_tab", resolved_target.to_cli(), _bool_arg(value=focus_window))

    def reload(self, *, tab: TabTarget | str | None = None) -> None:
        """Reload the target tab or active tab."""
        self._run_optional_tab_command(command="reload", tab=tab)

    def go_back(self, *, tab: TabTarget | str | None = None) -> None:
        """Navigate target tab back."""
        self._run_optional_tab_command(command="go_back", tab=tab)

    def go_forward(self, *, tab: TabTarget | str | None = None) -> None:
        """Navigate target tab forward."""
        self._run_optional_tab_command(command="go_forward", tab=tab)

    def stop(self, *, tab: TabTarget | str | None = None) -> None:
        """Stop loading in target tab."""
        self._run_optional_tab_command(command="stop", tab=tab)

    def source(self, *, tab: TabTarget | str | None = None) -> str:
        """Return HTML source for target tab."""
        args: tuple[str, ...] = ()
        if tab is not None:
            args = (self._tab_target(target=tab).to_cli(),)
        data = self._run("source", *args)
        return _as_str(value=data, field_name="source")

    def execute_javascript(self, javascript: str, *, tab: TabTarget | str | None = None) -> str:
        """Execute JavaScript and return raw string result."""
        args: tuple[str, ...] = (javascript,)
        if tab is not None:
            args = (javascript, self._tab_target(target=tab).to_cli())
        data = self._run("execute_js", *args)
        return _as_str(value=data, field_name="execute_js")

    def execute_javascript_json(
        self, javascript: str, *, tab: TabTarget | str | None = None
    ) -> JsonValue:
        """Execute JavaScript and parse its JSON output."""
        wrapped_javascript = f"JSON.stringify((function(){{ return ({javascript}); }})())"
        raw_result = self.execute_javascript(wrapped_javascript, tab=tab)
        try:
            decoded = cast("object", json.loads(raw_result))
        except json.JSONDecodeError as exc:
            raise AppleScriptDecodeError(raw_output=raw_result) from exc
        return self._coerce_json_value(decoded)

    def open_url(  # noqa: PLR0913
        self,
        url: str,
        *,
        new_window: bool = False,
        incognito: bool = False,
        window: WindowTarget | None = None,
        tab: TabTarget | str | None = None,
        activate: bool = True,
    ) -> ChromeTab:
        """Open URL according to targeting rules and return resulting tab."""
        if tab is not None:
            mode = "tab"
            target = self._tab_target(target=tab).to_cli()
        elif new_window or incognito:
            mode = "new_window"
            target = "incognito" if incognito else "normal"
        elif window is not None:
            mode = "window"
            target = window.window_id
        else:
            mode = "front"
            target = ""

        data = self._run("open_url", url, mode, target, _bool_arg(value=activate))
        return self._parse_tab(data)

    def close_tab(self, *, tab: TabTarget | str | None = None) -> None:
        """Close the target tab or active tab."""
        self._run_optional_tab_command(command="close_tab", tab=tab)

    def close_window(self, *, window: WindowTarget | None = None) -> None:
        """Close target window or front window."""
        args: tuple[str, ...] = ()
        if window is not None:
            args = (window.window_id,)
        self._run("close_window", *args)

    def window_bounds(self, *, window: WindowTarget | None = None) -> WindowBounds:
        """Get bounds for target window or front window."""
        args: tuple[str, ...] = ()
        if window is not None:
            args = (window.window_id,)
        data = self._run("get_window_bounds", *args)
        return self._parse_bounds(data)

    def set_window_bounds(
        self, bounds: WindowBounds, *, window: WindowTarget | None = None
    ) -> None:
        """Set bounds for target window or front window."""
        window_id = ""
        if window is not None:
            window_id = window.window_id
        self._run(
            "set_window_bounds",
            window_id,
            str(bounds.left),
            str(bounds.top),
            str(bounds.right),
            str(bounds.bottom),
        )

    def bookmarks_tree(self) -> ChromeBookmarks:
        """Return full bookmarks tree."""
        data = self._run("bookmarks_tree")
        payload = _as_dict(value=data, context="bookmarks_tree")
        return ChromeBookmarks(
            bookmarks_bar=self._parse_bookmark_folder(
                payload.get("bookmarks_bar"), "bookmarks_bar"
            ),
            other_bookmarks=self._parse_bookmark_folder(
                payload.get("other_bookmarks"),
                "other_bookmarks",
            ),
        )

    def _run(self, command: str, *args: str) -> JsonValue:
        backend = ChromeAppleScriptBackend(
            apple_script_executor=self.apple_script_executor,
            bundle_identifier=self.bundle_identifier,
        )
        return backend.run(command, *args)

    def _run_optional_tab_command(self, *, command: str, tab: TabTarget | str | None) -> None:
        args: tuple[str, ...] = ()
        if tab is not None:
            args = (self._tab_target(target=tab).to_cli(),)
        self._run(command, *args)

    def _parse_window(self, value: JsonValue) -> ChromeWindow:
        payload = _as_dict(value=value, context="window")
        return ChromeWindow(
            id=_as_id(value=payload.get("id"), field_name="id"),
            index=_as_int(value=payload.get("index"), field_name="index"),
            name=_as_str(value=payload.get("name"), field_name="name"),
            given_name=_as_str(value=payload.get("given_name"), field_name="given_name"),
            bounds=self._parse_bounds(payload.get("bounds")),
            closeable=_as_bool(value=payload.get("closeable"), field_name="closeable"),
            minimizable=_as_bool(value=payload.get("minimizable"), field_name="minimizable"),
            minimized=_as_bool(value=payload.get("minimized"), field_name="minimized"),
            resizable=_as_bool(value=payload.get("resizable"), field_name="resizable"),
            visible=_as_bool(value=payload.get("visible"), field_name="visible"),
            zoomable=_as_bool(value=payload.get("zoomable"), field_name="zoomable"),
            zoomed=_as_bool(value=payload.get("zoomed"), field_name="zoomed"),
            mode=_as_str(value=payload.get("mode"), field_name="mode"),
            active_tab_index=_as_int(
                value=payload.get("active_tab_index"),
                field_name="active_tab_index",
            ),
            active_tab_id=_as_id(value=payload.get("active_tab_id"), field_name="active_tab_id"),
            tab_count=_as_int(value=payload.get("tab_count"), field_name="tab_count"),
        )

    def _parse_tab(self, value: JsonValue) -> ChromeTab:
        payload = _as_dict(value=value, context="tab")
        return ChromeTab(
            id=_as_id(value=payload.get("id"), field_name="id"),
            window_id=_as_id(value=payload.get("window_id"), field_name="window_id"),
            index=_as_int(value=payload.get("index"), field_name="index"),
            title=_as_str(value=payload.get("title"), field_name="title"),
            url=_as_str(value=payload.get("url"), field_name="url"),
            loading=_as_bool(value=payload.get("loading"), field_name="loading"),
            window_name=_as_str(value=payload.get("window_name"), field_name="window_name"),
            is_active=_as_bool(value=payload.get("is_active"), field_name="is_active"),
        )

    def _parse_bounds(self, value: JsonValue) -> WindowBounds:
        payload = _as_dict(value=value, context="bounds")
        return WindowBounds(
            left=_as_int(value=payload.get("left"), field_name="left"),
            top=_as_int(value=payload.get("top"), field_name="top"),
            right=_as_int(value=payload.get("right"), field_name="right"),
            bottom=_as_int(value=payload.get("bottom"), field_name="bottom"),
        )

    def _parse_bookmark_item(self, value: JsonValue, context: str) -> ChromeBookmarkItem:
        payload = _as_dict(value=value, context=context)
        return ChromeBookmarkItem(
            id=_as_id(value=payload.get("id"), field_name=f"{context}.id"),
            title=_as_str(value=payload.get("title"), field_name=f"{context}.title"),
            url=_as_str(value=payload.get("url"), field_name=f"{context}.url"),
            index=_as_int(value=payload.get("index"), field_name=f"{context}.index"),
        )

    def _parse_bookmark_folder(self, value: JsonValue, context: str) -> ChromeBookmarkFolder:
        payload = _as_dict(value=value, context=context)
        raw_folders = _as_list(value=payload.get("folders"), context=f"{context}.folders")
        raw_items = _as_list(value=payload.get("items"), context=f"{context}.items")
        return ChromeBookmarkFolder(
            id=_as_id(value=payload.get("id"), field_name=f"{context}.id"),
            title=_as_str(value=payload.get("title"), field_name=f"{context}.title"),
            index=_as_int(value=payload.get("index"), field_name=f"{context}.index"),
            folders=[
                self._parse_bookmark_folder(folder, f"{context}.folder") for folder in raw_folders
            ],
            items=[self._parse_bookmark_item(item, f"{context}.item") for item in raw_items],
        )

    def _tab_target(self, *, target: TabTarget | str) -> TabTarget:
        if isinstance(target, TabTarget):
            return target
        return TabTarget.parse(target)

    def _coerce_json_value(self, value: object) -> JsonValue:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, list):
            return [self._coerce_json_value(item) for item in value]
        if isinstance(value, dict):
            mapped: dict[str, JsonValue] = {}
            for key, item in value.items():
                if not isinstance(key, str):
                    msg = f"JSON object keys must be strings, got {type(key)!r}."
                    raise ChromeError(msg)
                mapped[key] = self._coerce_json_value(item)
            return mapped
        msg = f"Unsupported JSON value type: {type(value)!r}."
        raise ChromeError(msg)


def _as_dict(*, value: JsonValue | None, context: str) -> dict[str, JsonValue]:
    if isinstance(value, dict):
        return value
    msg = f"Expected object for {context}."
    raise ChromeError(msg)


def _as_list(*, value: JsonValue | None, context: str) -> list[JsonValue]:
    if isinstance(value, list):
        return value
    msg = f"Expected array for {context}."
    raise ChromeError(msg)


def _as_str(*, value: JsonValue | None, field_name: str) -> str:
    if isinstance(value, str):
        return value
    msg = f"Expected string for field '{field_name}'."
    raise ChromeError(msg)


def _as_id(*, value: JsonValue | None, field_name: str) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        msg = f"Expected id-compatible value for field '{field_name}'."
        raise ChromeError(msg)
    if isinstance(value, (int, float)):
        return str(int(value))
    msg = f"Expected id-compatible value for field '{field_name}'."
    raise ChromeError(msg)


def _as_int(*, value: JsonValue | None, field_name: str) -> int:
    if isinstance(value, bool):
        msg = f"Expected integer for field '{field_name}'."
        raise ChromeError(msg)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError as exc:
            msg = f"Expected integer for field '{field_name}'."
            raise ChromeError(msg) from exc
    msg = f"Expected integer for field '{field_name}'."
    raise ChromeError(msg)


def _as_bool(*, value: JsonValue | None, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1"}:
            return True
        if normalized in {"false", "0"}:
            return False
    if isinstance(value, int):
        if value == 1:
            return True
        if value == 0:
            return False
    msg = f"Expected boolean for field '{field_name}'."
    raise ChromeError(msg)


def _bool_arg(*, value: bool) -> str:
    return "1" if value else "0"
