from __future__ import annotations

import json
from typing import cast

import pytest

from achrome.core._internal.apple_script import AppleScriptRunner
from achrome.core._internal.context import Context
from achrome.core._internal.tab_commands import NOT_FOUND_SENTINEL
from achrome.core.exceptions import DoesNotExistError
from achrome.core.tabs import Tab
from achrome.core.windows import Bounds, Window


class _SpyAppleScriptRunner:
    def __init__(self, response: str) -> None:
        self.response = response
        self.run_calls = 0
        self.scripts: list[str] = []

    def run(self, script: str) -> str:
        self.run_calls += 1
        self.scripts.append(script)
        return self.response


def test_window_properties_fetch_info_from_runner_each_access() -> None:
    runner = _SpyAppleScriptRunner(
        json.dumps(
            {
                "name": "Window 7",
                "bounds": [0, 0, 1280, 720],
                "index": 2,
                "closeable": True,
                "minimizable": True,
                "minimized": False,
                "resizable": True,
                "visible": True,
                "zoomable": True,
                "zoomed": False,
                "mode": "normal",
                "active_tab_index": 3,
                "presenting": False,
                "active_tab_id": 42,
            },
        ),
    )
    context = Context(runner=cast("AppleScriptRunner", runner))
    window = Window(id=7)
    window.set_context(context)

    assert window.name == "Window 7"
    assert "set targetWindowId to 7" in runner.scripts[-1]
    assert runner.run_calls == 1

    assert window.name == "Window 7"
    assert runner.run_calls == 2

    assert window.bounds == Bounds(0, 0, 1280, 720)
    assert window.index == 2
    assert window.closeable is True
    assert window.minimizable is True
    assert window.minimized is False
    assert window.resizable is True
    assert window.visible is True
    assert window.zoomable is True
    assert window.zoomed is False
    assert window.mode == "normal"
    assert window.active_tab_index == 3
    assert window.presenting is False
    assert window.active_tab_id == 42


def test_window_properties_raise_does_not_exist_on_not_found() -> None:
    runner = _SpyAppleScriptRunner(NOT_FOUND_SENTINEL)
    window = Window(id=7)
    window.set_context(Context(runner=cast("AppleScriptRunner", runner)))

    with pytest.raises(DoesNotExistError) as exc_info:
        _ = window.name

    assert str(exc_info.value) == "Cannot read window id=7: not found."


def test_tab_properties_fetch_info_from_runner_each_access() -> None:
    runner = _SpyAppleScriptRunner(
        json.dumps(
            {
                "title": "Tab 42",
                "url": "https://example.com",
                "loading": False,
                "is_active": True,
            },
        ),
    )
    context = Context(runner=cast("AppleScriptRunner", runner))
    tab = Tab(id=42, window_id=7)
    tab.set_context(context)

    assert tab.title == "Tab 42"
    assert "set targetWindowId to 7" in runner.scripts[-1]
    assert "set targetTabId to 42" in runner.scripts[-1]
    assert runner.run_calls == 1

    assert tab.title == "Tab 42"
    assert runner.run_calls == 2

    assert tab.url == "https://example.com"
    assert tab.loading is False
    assert tab.is_active is True


def test_tab_properties_raise_does_not_exist_on_not_found() -> None:
    runner = _SpyAppleScriptRunner(NOT_FOUND_SENTINEL)
    tab = Tab(id=42, window_id=7)
    tab.set_context(Context(runner=cast("AppleScriptRunner", runner)))

    with pytest.raises(DoesNotExistError) as exc_info:
        _ = tab.title

    assert str(exc_info.value) == "Cannot read tab id=42 in window id=7: not found."
