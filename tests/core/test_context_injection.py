from __future__ import annotations

import json
import re
import runpy
from typing import TYPE_CHECKING, cast
from unittest.mock import Mock, patch

import pytest

import achrome.core.chrome
from achrome.core._internal.apple_script import AppleScriptRunner
from achrome.core._internal.context import Context
from achrome.core.chrome import Chrome
from achrome.core.tabs import Tab, TabsManager
from achrome.core.windows import Bounds

if TYPE_CHECKING:
    from typing import Any


WINDOWS_JSON = json.dumps(
    [
        {
            "id": 1,
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
            "active_tab_id": "tab-1",
        },
        {
            "id": 2,
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
            "active_tab_id": "tab-2",
        },
    ],
)


def _tabs_json(window_id: int) -> str:
    return json.dumps(
        [
            {
                "id": "tab-1",
                "window_id": window_id,
                "name": "Tab 1",
                "title": "Tab 1",
                "url": "https://example.com",
                "loading": False,
                "is_active": True,
            },
            {
                "id": "tab-2",
                "window_id": window_id,
                "name": "Tab 2",
                "title": "Tab 2",
                "url": "https://example.com/2",
                "loading": False,
                "is_active": False,
            },
            {
                "id": "tab-3",
                "window_id": window_id,
                "name": "Tab 3",
                "title": "Tab 3",
                "url": "https://example.com/3",
                "loading": True,
                "is_active": False,
            },
        ],
    )


def _response_for_script(script: str) -> str:
    if "set targetWindowId to " not in script:
        return WINDOWS_JSON

    match = re.search(r"set targetWindowId to (\d+)", script)
    if match is None:
        return "[]"

    return _tabs_json(int(match.group(1)))


class _SpyAppleScriptRunner:
    def __init__(self, response: str | None = None) -> None:
        self.run_calls = 0
        self._response = response

    def run(self, script: str) -> str:
        self.run_calls += 1
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

    filtered_tabs_manager = tabs_manager.filter(name="Tab 1")

    assert isinstance(filtered_tabs_manager, TabsManager)
    assert filtered_tabs_manager._context is context
    assert filtered_tabs_manager._window_id == 1
    assert [tab.name for tab in filtered_tabs_manager.items] == ["Tab 1"]
    assert [tab.title for tab in filtered_tabs_manager.items] == ["Tab 1"]


def test_chrome_is_not_a_context_manager() -> None:
    chrome = cast("Any", Chrome())

    with pytest.raises(TypeError):
        with chrome:
            pass


def test_tab_source_and_execute_are_placeholder_values() -> None:
    tab = Tab(
        id="tab-1",
        window_id=1,
        name="Tab 1",
        title="Tab 1",
        url="https://example.com",
        loading=False,
    )
    tab._context = Mock()

    assert tab.source == "<html>...</html>"
    assert tab.execute("return document.title;") == "result of executing JavaScript"


def test_tabs_manager_raises_without_window_id() -> None:
    with pytest.raises(
        ValueError,
        match=r"TabsManager requires either _items or _window_id to be provided\.",
    ):
        TabsManager(_context=Context(runner=cast("AppleScriptRunner", _SpyAppleScriptRunner())))


def test_windows_loading_uses_runner_from_context() -> None:
    runner = _SpyAppleScriptRunner()
    chrome = Chrome()
    chrome._context = Context(runner=cast("AppleScriptRunner", runner))

    windows = chrome.windows.items

    assert [window.id for window in windows] == [1, 2]
    assert [window.name for window in windows] == ["Window 1", "Window 2"]
    assert windows[0].bounds == Bounds(0, 0, 1280, 720)
    assert windows[0].index == 1
    assert windows[0].closeable is True
    assert windows[0].minimizable is True
    assert windows[0].minimized is False
    assert windows[0].resizable is True
    assert windows[0].visible is True
    assert windows[0].zoomable is True
    assert windows[0].zoomed is False
    assert windows[0].mode == "normal"
    assert windows[0].active_tab_index == 1
    assert windows[0].presenting is False
    assert windows[0].active_tab_id == "tab-1"
    assert runner.run_calls == 1


def test_chrome_module_main_runs_from_entrypoint(capsys: pytest.CaptureFixture[str]) -> None:
    with patch.object(
        AppleScriptRunner,
        "run",
        side_effect=lambda *_args, **_kwargs: _response_for_script(str(_args[-1])),
    ):
        runpy.run_path(achrome.core.chrome.__file__, run_name="__main__")

    captured_stdout = capsys.readouterr().out

    assert "Window: Window 1 (id=1)" in captured_stdout
    assert (
        "Tab(id='tab-1', window_id=1, name='Tab 1', title='Tab 1', url='https://example.com'"
        in captured_stdout
    )
