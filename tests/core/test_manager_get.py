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

TAB_IDS_BY_WINDOW_ID: dict[int, list[int]] = {
    1: [101, 102, 103],
    2: [201, 202, 203],
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


def _response_for_script(script: str) -> str:
    response = "[]"

    if "set windowIds to current application's NSMutableArray's array()" in script:
        response = WINDOW_IDS_JSON
    elif "set windowRec to current application's NSMutableDictionary's dictionary()" in script:
        match = re.search(r"set targetWindowId to (\d+)", script)
        if match is not None:
            window_id = int(match.group(1))
            payload = WINDOW_INFO_BY_ID.get(window_id)
            response = json.dumps(payload) if payload is not None else "__ACHROME_NOT_FOUND__"
    elif "set tabIds to current application's NSMutableArray's array()" in script:
        match = re.search(r"set targetWindowId to (\d+)", script)
        if match is not None:
            window_id = int(match.group(1))
            response = json.dumps(TAB_IDS_BY_WINDOW_ID.get(window_id, []))
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

    tab = tabs_manager.get(id=101)

    assert isinstance(tab, Tab)
    assert tab.id == 101


def test_tabs_manager_get_raises_does_not_exist_for_missing_tab() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id=1)

    with pytest.raises(DoesNotExistError) as exc_info:
        tabs_manager.get(id=999)

    assert str(exc_info.value) == "TabsManager.get() found 0 objects for criteria {'id': 999}"


def test_tabs_manager_get_raises_multiple_objects_returned_for_non_unique_criteria() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id=1)

    with pytest.raises(MultipleObjectsReturnedError) as exc_info:
        tabs_manager.get(loading=False)

    assert (
        str(exc_info.value)
        == "TabsManager.get() found 2 objects for criteria {'loading': False}, expected 1"
    )


def test_tabs_manager_get_supports_title_contains_operator() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id=1)

    tab = tabs_manager.get(title__contains="Tab 2")

    assert tab.id == 102


def test_tabs_manager_get_supports_title_filters() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id=1)

    tab = tabs_manager.get(title__contains="Tab 3")

    assert tab.id == 103


def test_tabs_manager_get_supports_in_operator() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id=1)

    tab = tabs_manager.get(id__in=[102, 999])

    assert tab.id == 102


def test_tabs_manager_first_returns_first_tab() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id=1)

    tab = tabs_manager.first()

    assert tab.id == 101


def test_tabs_manager_last_returns_last_tab() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id=1)

    tab = tabs_manager.last()

    assert tab.id == 103


def test_tabs_manager_first_raises_does_not_exist_for_empty_filtered_result() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id=1)

    with pytest.raises(DoesNotExistError) as exc_info:
        tabs_manager.filter(id=999).first()

    assert str(exc_info.value) == "TabsManager.first() found 0 objects"


def test_tabs_manager_last_raises_does_not_exist_for_empty_filtered_result() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id=1)

    with pytest.raises(DoesNotExistError) as exc_info:
        tabs_manager.filter(id=999).last()

    assert str(exc_info.value) == "TabsManager.last() found 0 objects"


def test_tabs_manager_first_and_last_preserve_filtered_order() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id=1)
    filtered_tabs_manager = tabs_manager.filter(loading=False)

    assert filtered_tabs_manager.first().id == 101
    assert filtered_tabs_manager.last().id == 102


def test_tabs_manager_get_propagates_value_error_for_unsupported_operator() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id=1)

    with pytest.raises(ValueError, match="Unsupported operator: unknown"):
        cast("Any", tabs_manager).get(title__unknown="Tab")


def test_tabs_manager_active_returns_active_tab() -> None:
    runner = _SpyAppleScriptRunner(
        json.dumps({"title": "", "url": "", "loading": False, "is_active": True}),
    )
    context = _context(runner=cast("AppleScriptRunner", runner))
    active_tab = Tab(
        id=142,
        window_id=1,
    )
    active_tab._context = context
    tabs_manager = TabsManager(_context=context, _items=[active_tab])

    assert tabs_manager.active is active_tab


def test_tabs_manager_items_raises_runtime_error_without_window_id() -> None:
    context = _context()
    tab = Tab(
        id=101,
        window_id=1,
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


def test_windows_manager_first_returns_first_window() -> None:
    windows_manager = WindowsManager(_context=_context())

    window = windows_manager.first()

    assert window.id == 1


def test_windows_manager_last_returns_last_window() -> None:
    windows_manager = WindowsManager(_context=_context())

    window = windows_manager.last()

    assert window.id == 2


def test_window_active_tab_uses_active_tab_id_lookup() -> None:
    windows_manager = WindowsManager(_context=_context())
    window = windows_manager.get(id=1)

    assert window.active_tab.id == 101


def test_windows_manager_get_without_criteria_raises_multiple_objects_returned() -> None:
    windows_manager = WindowsManager(_context=_context())

    with pytest.raises(MultipleObjectsReturnedError) as exc_info:
        windows_manager.get()

    assert str(exc_info.value) == "WindowsManager.get() found 2 objects for criteria {}, expected 1"


def test_get_exceptions_inherit_from_achrome_error() -> None:
    assert issubclass(DoesNotExistError, AChromeError)
    assert issubclass(MultipleObjectsReturnedError, AChromeError)
