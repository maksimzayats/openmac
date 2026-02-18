from __future__ import annotations

import json
from typing import cast

import pytest
from openmac.core._internal.apple_scripts.runner import AppleScriptRunner
from openmac.core._internal.context import Context
from openmac.core._internal.tab_commands import NOT_FOUND_SENTINEL
from openmac.core.exceptions import DoesNotExistError
from openmac.core.tabs import Tab
from openmac.core.windows import Bounds, Window


class _SpyAppleScriptRunner:
    def __init__(self, responses: str | list[str]) -> None:
        if isinstance(responses, str):
            self._responses = [responses]
        else:
            self._responses = responses
        self.run_calls = 0
        self.scripts: list[str] = []

    def run(self, script: str) -> str:
        self.run_calls += 1
        self.scripts.append(script)
        if len(self._responses) > 1:
            return self._responses.pop(0)

        return self._responses[0]


def test_window_properties_use_hydrated_cache_without_runner_calls() -> None:
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

    window.refresh()
    assert "set targetWindowId to 7" in runner.scripts[-1]
    assert runner.run_calls == 1

    assert window.name == "Window 7"
    assert window.name == "Window 7"
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
    assert runner.run_calls == 1


def test_window_refresh_updates_cached_state() -> None:
    runner = _SpyAppleScriptRunner(
        [
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
            json.dumps(
                {
                    "name": "Window 7 updated",
                    "bounds": [10, 20, 640, 480],
                    "index": 1,
                    "closeable": True,
                    "minimizable": True,
                    "minimized": True,
                    "resizable": False,
                    "visible": False,
                    "zoomable": True,
                    "zoomed": True,
                    "mode": "incognito",
                    "active_tab_index": 1,
                    "presenting": True,
                    "active_tab_id": 99,
                },
            ),
        ],
    )
    window = Window(id=7)
    window.set_context(Context(runner=cast("AppleScriptRunner", runner)))

    window.refresh()
    assert window.name == "Window 7"
    assert runner.run_calls == 1

    window.refresh()
    assert window.name == "Window 7 updated"
    assert window.bounds == Bounds(10, 20, 640, 480)
    assert runner.run_calls == 2


def test_window_refresh_raises_does_not_exist_on_not_found() -> None:
    runner = _SpyAppleScriptRunner(NOT_FOUND_SENTINEL)
    window = Window(id=7)
    window.set_context(Context(runner=cast("AppleScriptRunner", runner)))

    with pytest.raises(DoesNotExistError) as exc_info:
        window.refresh()

    assert str(exc_info.value) == "Cannot read window id=7: not found."


def test_window_property_raises_clear_error_when_not_hydrated() -> None:
    runner = _SpyAppleScriptRunner("{}")
    window = Window(id=7)
    window.set_context(Context(runner=cast("AppleScriptRunner", runner)))

    with pytest.raises(RuntimeError) as exc_info:
        _ = window.name

    assert (
        str(exc_info.value)
        == "Window id=7 state is not hydrated. Call `window.refresh()` before accessing properties."
    )
    assert runner.run_calls == 0


def test_tab_properties_use_hydrated_cache_without_runner_calls() -> None:
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

    tab.refresh()
    assert "set targetWindowId to 7" in runner.scripts[-1]
    assert "set targetTabId to 42" in runner.scripts[-1]
    assert runner.run_calls == 1

    assert tab.title == "Tab 42"
    assert tab.title == "Tab 42"
    assert tab.url == "https://example.com"
    assert tab.loading is False
    assert tab.is_active is True
    assert runner.run_calls == 1


def test_tab_refresh_updates_cached_state() -> None:
    runner = _SpyAppleScriptRunner(
        [
            json.dumps(
                {
                    "title": "Loading",
                    "url": "https://example.com/loading",
                    "loading": True,
                    "is_active": True,
                },
            ),
            json.dumps(
                {
                    "title": "Ready",
                    "url": "https://example.com/ready",
                    "loading": False,
                    "is_active": True,
                },
            ),
        ],
    )
    tab = Tab(id=42, window_id=7)
    tab.set_context(Context(runner=cast("AppleScriptRunner", runner)))

    tab.refresh()
    assert tab.title == "Loading"
    assert runner.run_calls == 1

    tab.refresh()
    assert tab.title == "Ready"
    assert runner.run_calls == 2


def test_tab_refresh_raises_does_not_exist_on_not_found() -> None:
    runner = _SpyAppleScriptRunner(NOT_FOUND_SENTINEL)
    tab = Tab(id=42, window_id=7)
    tab.set_context(Context(runner=cast("AppleScriptRunner", runner)))

    with pytest.raises(DoesNotExistError) as exc_info:
        tab.refresh()

    assert str(exc_info.value) == "Cannot read tab id=42 in window id=7: not found."


def test_tab_property_raises_clear_error_when_not_hydrated() -> None:
    runner = _SpyAppleScriptRunner("{}")
    tab = Tab(id=42, window_id=7)
    tab.set_context(Context(runner=cast("AppleScriptRunner", runner)))

    with pytest.raises(RuntimeError) as exc_info:
        _ = tab.title

    assert (
        str(exc_info.value) == "Tab id=42 in window id=7 state is not hydrated. "
        "Call `tab.refresh()` before accessing properties."
    )
    assert runner.run_calls == 0
