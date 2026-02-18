from __future__ import annotations

import base64
import json
import re
from typing import TYPE_CHECKING, cast

import pytest

from achrome.core._internal.apple_script import AppleScriptRunner
from achrome.core._internal.context import Context
from achrome.core.chrome import Chrome
from achrome.core.tabs import Tab, TabsManager
from achrome.core.windows import Bounds

if TYPE_CHECKING:
    from typing import Any


WINDOW_INFO_BY_ID: dict[int, dict[str, object]] = {
    1: {
        "name": "Window 1",
        "bounds": [0, 0, 1280, 720],
        "index": 1,
        "closeable": True,
        "minimizable": True,
        "minimized": False,
        "resizable": True,
        "visible": True,
        "zoomable": True,
        "zoomed": False,
        "mode": "normal",
        "active_tab_index": 1,
        "presenting": False,
        "active_tab_id": 101,
    },
    2: {
        "name": "Window 2",
        "bounds": [100, 80, 1024, 768],
        "index": 2,
        "closeable": True,
        "minimizable": True,
        "minimized": True,
        "resizable": True,
        "visible": False,
        "zoomable": True,
        "zoomed": True,
        "mode": "incognito",
        "active_tab_index": 2,
        "presenting": True,
        "active_tab_id": 202,
    },
}
TAB_INFO_BY_WINDOW_AND_ID: dict[tuple[int, int], dict[str, object]] = {
    (1, 101): {"title": "Tab 1", "url": "https://example.com", "loading": False, "is_active": True},
    (1, 102): {
        "title": "Tab 2",
        "url": "https://example.com/2",
        "loading": False,
        "is_active": False,
    },
    (1, 103): {
        "title": "Tab 3",
        "url": "https://example.com/3",
        "loading": True,
        "is_active": False,
    },
    (2, 201): {
        "title": "Tab 1",
        "url": "https://example.com",
        "loading": False,
        "is_active": False,
    },
    (2, 202): {
        "title": "Tab 2",
        "url": "https://example.com/2",
        "loading": False,
        "is_active": True,
    },
    (2, 203): {
        "title": "Tab 3",
        "url": "https://example.com/3",
        "loading": True,
        "is_active": False,
    },
}
WINDOW_LIST_JSON = json.dumps(
    [
        {
            "id": window_id,
            **window_info,
        }
        for window_id, window_info in WINDOW_INFO_BY_ID.items()
    ],
)
TAB_LIST_BY_WINDOW_ID: dict[int, list[dict[str, object]]] = {
    window_id: [
        {
            "id": tab_id,
            **TAB_INFO_BY_WINDOW_AND_ID[window_id, tab_id],
        }
        for (tab_window_id, tab_id), _ in TAB_INFO_BY_WINDOW_AND_ID.items()
        if tab_window_id == window_id
    ]
    for window_id in WINDOW_INFO_BY_ID
}


def _response_for_script(script: str) -> str:
    response = "[]"

    if "set windowRecs to current application's NSMutableArray's array()" in script:
        response = WINDOW_LIST_JSON
    elif "set windowRec to current application's NSMutableDictionary's dictionary()" in script:
        match = re.search(r"set targetWindowId to (\d+)", script)
        if match is not None:
            window_id = int(match.group(1))
            payload = WINDOW_INFO_BY_ID.get(window_id)
            response = json.dumps(payload) if payload is not None else "__ACHROME_NOT_FOUND__"
    elif "set tabRecs to current application's NSMutableArray's array()" in script:
        match = re.search(r"set targetWindowId to (\d+)", script)
        if match is not None:
            window_id = int(match.group(1))
            response = json.dumps(TAB_LIST_BY_WINDOW_ID.get(window_id, []))
    elif "set targetTabId to " in script:
        window_match = re.search(r"set targetWindowId to (\d+)", script)
        tab_match = re.search(r"set targetTabId to (\d+)", script)
        if window_match is not None and tab_match is not None:
            key = (int(window_match.group(1)), int(tab_match.group(1)))
            payload = TAB_INFO_BY_WINDOW_AND_ID.get(key)
            response = json.dumps(payload) if payload is not None else "__ACHROME_NOT_FOUND__"

    return response


class _SpyAppleScriptRunner:
    def __init__(self, response: str | None = None) -> None:
        self.run_calls = 0
        self.scripts: list[str] = []
        self._response = response

    def run(self, script: str) -> str:
        self.run_calls += 1
        self.scripts.append(script)
        if self._response is not None:
            return self._response

        return _response_for_script(script)


def test_chrome_windows_construct_managers_with_shared_context() -> None:
    runner = _SpyAppleScriptRunner()
    context_runner = cast("AppleScriptRunner", runner)
    chrome = Chrome()
    chrome._context = Context(runner=context_runner)

    windows_manager = chrome.windows
    second_windows_manager = chrome.windows

    assert windows_manager._context is second_windows_manager._context
    assert windows_manager._context.runner is context_runner


def test_window_tabs_use_same_context_instance() -> None:
    chrome = Chrome()
    chrome._context = Context(runner=cast("AppleScriptRunner", _SpyAppleScriptRunner()))
    windows_manager = chrome.windows

    windows = windows_manager.items

    assert windows
    assert all(window.tabs._context is windows_manager._context for window in windows)
    assert all(window.tabs._window_id == window.id for window in windows)


def test_chrome_tabs_aggregation_uses_required_context() -> None:
    runner = _SpyAppleScriptRunner()
    chrome = Chrome()
    chrome._context = Context(runner=cast("AppleScriptRunner", runner))

    tabs_manager = chrome.tabs

    assert tabs_manager._context is chrome.windows._context
    assert len(tabs_manager.items) == 6
    assert {tab.window_id for tab in tabs_manager.items} == {1, 2}
    assert runner.run_calls == 3


def test_filter_preserves_context_and_manager_specific_fields() -> None:
    context = Context(runner=cast("AppleScriptRunner", _SpyAppleScriptRunner()))
    tabs_manager = TabsManager(_context=context, _window_id=1)

    filtered_tabs_manager = tabs_manager.filter(title="Tab 1")

    assert isinstance(filtered_tabs_manager, TabsManager)
    assert filtered_tabs_manager._context is context
    assert filtered_tabs_manager._window_id == 1
    assert [tab.title for tab in filtered_tabs_manager.items] == ["Tab 1"]


def test_chrome_is_not_a_context_manager() -> None:
    chrome = cast("Any", Chrome())

    with pytest.raises(TypeError):
        with chrome:
            pass


def test_tab_source_uses_execute_and_returns_runner_value() -> None:
    runner = _SpyAppleScriptRunner(response="<html>DOM</html>")
    tab = Tab(
        id=101,
        window_id=1,
    )
    tab._context = Context(runner=cast("AppleScriptRunner", runner))
    source_javascript_base64 = base64.b64encode(
        b"document.documentElement.outerHTML",
    ).decode("ascii")

    assert tab.execute("return document.title;") == "<html>DOM</html>"
    assert tab.source == "<html>DOM</html>"
    assert any(
        f'set jsBase64 to "{source_javascript_base64}"' in script for script in runner.scripts
    )


def test_tabs_manager_raises_without_window_id() -> None:
    with pytest.raises(
        ValueError,
        match=r"TabsManager requires either _items or _window_id to be provided\.",
    ):
        TabsManager(_context=Context(runner=cast("AppleScriptRunner", _SpyAppleScriptRunner())))


def test_global_tabs_manager_allows_empty_items_and_filtering() -> None:
    context = Context(runner=cast("AppleScriptRunner", _SpyAppleScriptRunner()))
    tabs_manager = TabsManager(_context=context, _items=[])

    assert tabs_manager.items == []
    assert tabs_manager.filter(title="anything").items == []


def test_windows_loading_uses_runner_from_context() -> None:
    runner = _SpyAppleScriptRunner()
    chrome = Chrome()
    chrome._context = Context(runner=cast("AppleScriptRunner", runner))

    windows = chrome.windows.items

    assert [window.id for window in windows] == [1, 2]
    assert runner.run_calls == 1

    assert windows[0].name == "Window 1"
    assert runner.run_calls == 1
    assert windows[0].name == "Window 1"
    assert runner.run_calls == 1

    assert windows[0].bounds == Bounds(0, 0, 1280, 720)
    assert runner.run_calls == 1
