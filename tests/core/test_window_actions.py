from __future__ import annotations

import json
from collections.abc import Callable
from typing import cast

import pytest

from achrome.core._internal.apple_script import AppleScriptRunner
from achrome.core._internal.context import Context
from achrome.core._internal.tab_commands import NOT_FOUND_SENTINEL
from achrome.core.exceptions import DoesNotExistError
from achrome.core.windows import Bounds, Window, WindowsManager

WINDOW_IDS_JSON = json.dumps([1, 2])
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


class _SpyAppleScriptRunner:
    def __init__(self, response: str | None = None) -> None:
        self.response = response
        self.scripts: list[str] = []

    def run(self, script: str) -> str:
        self.scripts.append(script)
        if self.response is not None:
            return self.response

        if "set windowIds to current application's NSMutableArray's array()" in script:
            return WINDOW_IDS_JSON

        if "set windowRec to current application's NSMutableDictionary's dictionary()" in script:
            for window_id, payload in WINDOW_INFO_BY_ID.items():
                if f"set targetWindowId to {window_id}" in script:
                    return json.dumps(payload)
            return NOT_FOUND_SENTINEL

        return "ok"


def _make_context(response: str) -> tuple[Context, _SpyAppleScriptRunner]:
    runner = _SpyAppleScriptRunner(response)
    return Context(runner=cast("AppleScriptRunner", runner)), runner


def _make_window(*, response: str = "ok") -> tuple[Window, _SpyAppleScriptRunner]:
    context, runner = _make_context(response)
    window = Window(id=7)
    window.set_context(context)
    return window, runner


@pytest.mark.parametrize(
    ("operation", "expected_command"),
    [
        ("close", "close targetWindow"),
        ("activate", "set index of targetWindow to 1"),
        ("activate", "activate"),
        ("minimize", "set minimized of targetWindow to true"),
        ("unminimize", "set minimized of targetWindow to false"),
        ("show", "set visible of targetWindow to true"),
        ("hide", "set visible of targetWindow to false"),
        ("zoom", "set zoomed of targetWindow to true"),
        ("unzoom", "set zoomed of targetWindow to false"),
        ("enter_presentation_mode", "enter presentation mode targetWindow"),
        ("exit_presentation_mode", "exit presentation mode targetWindow"),
    ],
)
def test_window_void_actions_emit_expected_script(operation: str, expected_command: str) -> None:
    window, runner = _make_window()

    getattr(window, operation)()

    script = runner.scripts[-1]
    assert "set targetWindowId to 7" in script
    assert expected_command in script


def test_window_set_bounds_emits_expected_script() -> None:
    window, runner = _make_window()

    window.set_bounds(Bounds(11, 22, 333, 444))

    script = runner.scripts[-1]
    assert "set targetWindowId to 7" in script
    assert "set bounds of targetWindow to {11, 22, 333, 444}" in script


def test_window_activate_tab_index_emits_expected_script() -> None:
    window, runner = _make_window()

    window.activate_tab_index(3)

    script = runner.scripts[-1]
    assert "set targetWindowId to 7" in script
    assert "set active tab index of targetWindow to 3" in script
    assert "activate" in script


def test_window_activate_tab_uses_tab_lookup_script() -> None:
    window, runner = _make_window()

    window.activate_tab(901)

    script = runner.scripts[-1]
    assert "set targetWindowId to 7" in script
    assert "set targetTabId to 901" in script
    assert "set active tab index of targetWindow to tabIndex" in script
    assert "activate" in script


@pytest.mark.parametrize(
    ("invoker", "action"),
    [
        (lambda window: window.close(), "close"),
        (lambda window: window.activate(), "activate"),
        (lambda window: window.set_bounds(Bounds(1, 2, 3, 4)), "set bounds"),
        (lambda window: window.minimize(), "minimize"),
        (lambda window: window.unminimize(), "unminimize"),
        (lambda window: window.show(), "show"),
        (lambda window: window.hide(), "hide"),
        (lambda window: window.zoom(), "zoom"),
        (lambda window: window.unzoom(), "unzoom"),
        (
            lambda window: window.enter_presentation_mode(),
            "enter presentation mode",
        ),
        (
            lambda window: window.exit_presentation_mode(),
            "exit presentation mode",
        ),
    ],
)
def test_window_void_actions_raise_does_not_exist_on_not_found(
    invoker: Callable[[Window], None],
    action: str,
) -> None:
    window, _runner = _make_window(response=NOT_FOUND_SENTINEL)

    with pytest.raises(DoesNotExistError) as exc_info:
        invoker(window)

    assert str(exc_info.value) == f"Cannot {action} window id=7: not found."


def test_window_activate_tab_index_raises_does_not_exist_on_not_found() -> None:
    window, _runner = _make_window(response=NOT_FOUND_SENTINEL)

    with pytest.raises(DoesNotExistError) as exc_info:
        window.activate_tab_index(3)

    assert str(exc_info.value) == "Cannot activate tab index=3 in window id=7: not found."


def test_window_activate_tab_raises_does_not_exist_on_not_found() -> None:
    window, _runner = _make_window(response=NOT_FOUND_SENTINEL)

    with pytest.raises(DoesNotExistError) as exc_info:
        window.activate_tab(901)

    assert str(exc_info.value) == "Cannot activate tab id=901 in window id=7: not found."


def test_windows_manager_front_returns_window_with_index_one() -> None:
    runner = _SpyAppleScriptRunner()
    context = Context(runner=cast("AppleScriptRunner", runner))
    windows_manager = WindowsManager(_context=context)

    front_window = windows_manager.front

    assert front_window.id == 1


def test_windows_manager_create_incognito_returns_window_with_context_and_tabs() -> None:
    context, runner = _make_context("55")
    windows_manager = WindowsManager(_context=context)

    window = windows_manager.create(mode="incognito")

    script = runner.scripts[-1]
    assert window.id == 55
    assert window._context is context
    assert window.tabs._window_id == window.id
    assert window.tabs._context is context
    assert "make new window" in script
    assert 'with properties {mode:"incognito"}' in script


def test_windows_manager_create_normal_uses_default_window_mode() -> None:
    context, runner = _make_context("56")
    windows_manager = WindowsManager(_context=context)

    window = windows_manager.create()

    script = runner.scripts[-1]
    assert window.id == 56
    assert window._context is context
    assert window.tabs._window_id == window.id
    assert window.tabs._context is context
    assert "set targetWindow to make new window" in script
    assert 'with properties {mode:"incognito"}' not in script
