from __future__ import annotations

import json
import re
from typing import Any, cast

import pytest

from achrome.core._internal.apple_script import AppleScriptRunner
from achrome.core._internal.context import Context
from achrome.core.exceptions import AChromeError, DoesNotExistError, MultipleObjectsReturnedError
from achrome.core.tabs import Tab, TabsManager
from achrome.core.windows import Bounds, Window, WindowsManager

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
        self._response = response

    def run(self, script: str) -> str:
        if self._response is not None:
            return self._response

        return _response_for_script(script)


def _context(runner: AppleScriptRunner | None = None) -> Context:
    context_runner = runner or cast("AppleScriptRunner", _SpyAppleScriptRunner())
    return Context(runner=context_runner)


def test_tabs_manager_get_returns_unique_tab_by_id() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id=1)

    tab = tabs_manager.get(id="tab-1")

    assert isinstance(tab, Tab)
    assert tab.id == "tab-1"


def test_tabs_manager_get_raises_does_not_exist_for_missing_tab() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id=1)

    with pytest.raises(DoesNotExistError) as exc_info:
        tabs_manager.get(id="missing")

    assert str(exc_info.value) == "TabsManager.get() found 0 objects for criteria {'id': 'missing'}"


def test_tabs_manager_get_raises_multiple_objects_returned_for_non_unique_criteria() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id=1)

    with pytest.raises(MultipleObjectsReturnedError) as exc_info:
        tabs_manager.get(loading=False)

    assert (
        str(exc_info.value)
        == "TabsManager.get() found 2 objects for criteria {'loading': False}, expected 1"
    )


def test_tabs_manager_get_supports_contains_operator() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id=1)

    tab = tabs_manager.get(name__contains="Tab 2")

    assert tab.id == "tab-2"


def test_tabs_manager_get_supports_title_filters() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id=1)

    tab = tabs_manager.get(title__contains="Tab 3")

    assert tab.id == "tab-3"


def test_tabs_manager_get_supports_in_operator() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id=1)

    tab = tabs_manager.get(id__in=["tab-2", "tab-99"])

    assert tab.id == "tab-2"


def test_tabs_manager_get_propagates_value_error_for_unsupported_operator() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id=1)

    with pytest.raises(ValueError, match="Unsupported operator: unknown"):
        cast("Any", tabs_manager).get(name__unknown="Tab")


def test_tabs_manager_active_returns_active_tab() -> None:
    context = _context()
    active_tab = Tab(
        id="tab-42",
        window_id=1,
        name="Active Tab",
        title="Active Tab",
        url="https://example.com/active",
        loading=False,
        is_active=True,
    )
    active_tab._context = context
    tabs_manager = TabsManager(_context=context, _items=[active_tab])

    assert tabs_manager.active is active_tab


def test_tabs_manager_items_raises_runtime_error_without_window_id() -> None:
    context = _context()
    tab = Tab(
        id="tab-1",
        window_id=1,
        name="Tab 1",
        title="Tab 1",
        url="https://example.com",
        loading=False,
    )
    tab._context = context
    tabs_manager = TabsManager(_context=context, _items=[tab])
    tabs_manager._items = None

    with pytest.raises(RuntimeError, match=r"Cannot load tabs without a window id\."):
        _ = tabs_manager.items


def test_windows_manager_get_returns_unique_window_by_id() -> None:
    windows_manager = WindowsManager(_context=_context())

    window = windows_manager.get(id=1)

    assert isinstance(window, Window)
    assert window.id == 1


def test_windows_manager_get_supports_bounds_filters() -> None:
    windows_manager = WindowsManager(_context=_context())

    window_by_bounds = windows_manager.get(bounds=Bounds(100, 80, 1024, 768))
    window_by_member = windows_manager.get(bounds__contains=1280)

    assert window_by_bounds.id == 2
    assert window_by_member.id == 1


def test_windows_manager_defaults_invalid_bounds_shape_to_zero_tuple() -> None:
    windows_payload = json.dumps(
        [
            {
                "id": 1,
                "name": "Window 1",
                "bounds": [1, 2, 3],
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
        ],
    )
    windows_manager = WindowsManager(
        _context=_context(runner=cast("AppleScriptRunner", _SpyAppleScriptRunner(windows_payload))),
    )

    window = windows_manager.get(id=1)

    assert window.bounds == Bounds(0, 0, 0, 0)


def test_windows_manager_get_without_criteria_raises_multiple_objects_returned() -> None:
    windows_manager = WindowsManager(_context=_context())

    with pytest.raises(MultipleObjectsReturnedError) as exc_info:
        windows_manager.get()

    assert str(exc_info.value) == "WindowsManager.get() found 2 objects for criteria {}, expected 1"


def test_get_exceptions_inherit_from_achrome_error() -> None:
    assert issubclass(DoesNotExistError, AChromeError)
    assert issubclass(MultipleObjectsReturnedError, AChromeError)
