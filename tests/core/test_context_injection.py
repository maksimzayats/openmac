from __future__ import annotations

import runpy
from typing import TYPE_CHECKING, cast

import pytest

import achrome.core.chrome
from achrome.core._internal.chome_api import ChromeAPI
from achrome.core._internal.context import Context
from achrome.core.chrome import Chrome
from achrome.core.tabs import Tab, TabsManager

if TYPE_CHECKING:
    from typing import Any


class _SpyChromeAPI(ChromeAPI):
    def __init__(self) -> None:
        self.get_windows_calls = 0

    def get_windows(self) -> list[object]:
        self.get_windows_calls += 1
        return []


def test_chrome_windows_construct_managers_with_shared_context() -> None:
    chrome_api = _SpyChromeAPI()
    chrome = Chrome(chrome_api=chrome_api)

    windows_manager = chrome.windows
    second_windows_manager = chrome.windows

    assert windows_manager._context is second_windows_manager._context
    assert windows_manager._context.chrome_api is chrome_api


def test_window_tabs_use_same_context_instance() -> None:
    chrome = Chrome(chrome_api=_SpyChromeAPI())
    windows_manager = chrome.windows

    windows = windows_manager.items

    assert windows
    assert all(window.tabs._context is windows_manager._context for window in windows)


def test_chrome_tabs_aggregation_uses_required_context() -> None:
    chrome_api = _SpyChromeAPI()
    chrome = Chrome(chrome_api=chrome_api)

    tabs_manager = chrome.tabs

    assert tabs_manager._context is chrome.windows._context
    assert len(tabs_manager.items) == 6
    assert {tab.window_id for tab in tabs_manager.items} == {"window-1", "window-2"}
    assert chrome_api.get_windows_calls == 1


def test_filter_preserves_context_and_manager_specific_fields() -> None:
    context = Context(chrome_api=_SpyChromeAPI())
    tabs_manager = TabsManager(_context=context, _window_id="window-1")

    filtered_tabs_manager = tabs_manager.filter(name="Tab 1")

    assert isinstance(filtered_tabs_manager, TabsManager)
    assert filtered_tabs_manager._context is context
    assert filtered_tabs_manager._window_id == "window-1"
    assert [tab.name for tab in filtered_tabs_manager.items] == ["Tab 1"]


def test_chrome_is_not_a_context_manager() -> None:
    chrome = cast("Any", Chrome(chrome_api=_SpyChromeAPI()))

    with pytest.raises(TypeError):
        with chrome:
            pass


def test_tab_source_and_execute_are_placeholder_values() -> None:
    tab = Tab(
        id="tab-1",
        window_id="window-1",
        name="Tab 1",
        url="https://example.com",
        loading=False,
    )

    assert tab.source == "<html>...</html>"
    assert tab.execute("return document.title;") == "result of executing JavaScript"


def test_tabs_manager_raises_without_window_id() -> None:
    tabs_manager = TabsManager(_context=Context(chrome_api=_SpyChromeAPI()))

    with pytest.raises(RuntimeError, match=r"Cannot load tabs without a window id\."):
        _ = tabs_manager.items


def test_chrome_open_returns_placeholder_tab() -> None:
    chrome = Chrome(chrome_api=_SpyChromeAPI())

    tab = chrome.open(
        "https://example.dev",
        window_id="window-2",
        new_window=True,
        incognito=True,
        tab_id="tab-5",
    )

    assert tab.id == "new-tab-id"
    assert tab.window_id == "window-1"
    assert tab.name == "New Tab"
    assert tab.url == "https://example.dev"
    assert tab.loading is True


def test_chrome_api_placeholder_methods_return_empty_lists() -> None:
    chrome_api = ChromeAPI()

    assert chrome_api.get_windows() == []
    assert chrome_api.get_tabs() == []


def test_chrome_module_main_runs_from_entrypoint(capsys: pytest.CaptureFixture[str]) -> None:
    runpy.run_path(achrome.core.chrome.__file__, run_name="__main__")

    captured_stdout = capsys.readouterr().out

    assert "Window: Window 1 (id=window-1)" in captured_stdout
    assert "Tab: Tab 1 (id=tab-1, url=https://example.com, wid=window-1)" in captured_stdout
