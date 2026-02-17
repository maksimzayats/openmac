from __future__ import annotations

from typing import Any, cast

import pytest

from achrome.core._internal.chome_api import ChromeAPI
from achrome.core._internal.context import Context
from achrome.core.exceptions import AChromeError, DoesNotExistError, MultipleObjectsReturnedError
from achrome.core.tabs import Tab, TabsManager
from achrome.core.windows import Window, WindowsManager


def _context() -> Context:
    return Context(chrome_api=ChromeAPI())


def test_tabs_manager_get_returns_unique_tab_by_id() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id="window-1")

    tab = tabs_manager.get(id="tab-1")

    assert isinstance(tab, Tab)
    assert tab.id == "tab-1"


def test_tabs_manager_get_raises_does_not_exist_for_missing_tab() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id="window-1")

    with pytest.raises(DoesNotExistError) as exc_info:
        tabs_manager.get(id="missing")

    assert str(exc_info.value) == "TabsManager.get() found 0 objects for criteria {'id': 'missing'}"


def test_tabs_manager_get_raises_multiple_objects_returned_for_non_unique_criteria() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id="window-1")

    with pytest.raises(MultipleObjectsReturnedError) as exc_info:
        tabs_manager.get(loading=False)

    assert (
        str(exc_info.value)
        == "TabsManager.get() found 2 objects for criteria {'loading': False}, expected 1"
    )


def test_tabs_manager_get_supports_contains_operator() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id="window-1")

    tab = tabs_manager.get(name__contains="Tab 2")

    assert tab.id == "tab-2"


def test_tabs_manager_get_supports_in_operator() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id="window-1")

    tab = tabs_manager.get(id__in=["tab-2", "tab-99"])

    assert tab.id == "tab-2"


def test_tabs_manager_get_propagates_value_error_for_unsupported_operator() -> None:
    tabs_manager = TabsManager(_context=_context(), _window_id="window-1")

    with pytest.raises(ValueError, match="Unsupported operator: unknown"):
        cast("Any", tabs_manager).get(name__unknown="Tab")


def test_windows_manager_get_returns_unique_window_by_id() -> None:
    windows_manager = WindowsManager(_context=_context())

    window = windows_manager.get(id="window-1")

    assert isinstance(window, Window)
    assert window.id == "window-1"


def test_windows_manager_get_without_criteria_raises_multiple_objects_returned() -> None:
    windows_manager = WindowsManager(_context=_context())

    with pytest.raises(MultipleObjectsReturnedError) as exc_info:
        windows_manager.get()

    assert str(exc_info.value) == "WindowsManager.get() found 2 objects for criteria {}, expected 1"


def test_get_exceptions_inherit_from_achrome_error() -> None:
    assert issubclass(DoesNotExistError, AChromeError)
    assert issubclass(MultipleObjectsReturnedError, AChromeError)
