from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import pytest

from openmac.apps.browsers.chrome.objects.tabs import (
    ChromeTab,
    ChromeWindowsTabsManager,
    ChromeWindowTabsManager,
)

if TYPE_CHECKING:
    from openmac import ChromeWindow
    from openmac.apps.browsers.chrome.objects.windows import ChromeWindowsManager


@dataclass(slots=True)
class FakeTab:
    url: str
    wait_calls: int = 0

    def wait_until_loaded(self) -> None:
        self.wait_calls += 1


@dataclass(slots=True)
class FakeWindowTabsManager:
    tab: ChromeTab
    called_with: tuple[str, bool, bool] | None = None

    def open(
        self,
        url: str,
        *,
        wait_until_loaded: bool = True,
        preserve_focus: bool = True,
    ) -> ChromeTab:
        self.called_with = (url, wait_until_loaded, preserve_focus)
        return self.tab


@dataclass(slots=True)
class FakeWindow:
    tabs: FakeWindowTabsManager


@dataclass(slots=True)
class FakeWindowsManager:
    first: FakeWindow


def test_windows_tabs_open_delegates_to_first_window_tabs_manager() -> None:
    expected_tab = cast("ChromeTab", object())
    window_tabs = FakeWindowTabsManager(tab=expected_tab)
    manager = ChromeWindowsTabsManager(
        from_windows=cast(
            "ChromeWindowsManager",
            FakeWindowsManager(first=FakeWindow(tabs=window_tabs)),
        ),
    )

    actual_tab = manager.open(
        url="https://www.google.com",
        wait_until_loaded=False,
        preserve_focus=False,
    )

    assert actual_tab is expected_tab
    assert window_tabs.called_with == ("https://www.google.com", False, False)


def test_window_tabs_get_or_open_returns_existing_tab() -> None:
    existing_tab = FakeTab(url="https://www.google.com")
    expected_tab = cast("ChromeTab", existing_tab)
    manager = ChromeWindowTabsManager(
        from_window=cast("ChromeWindow", object()),
        _loaded=True,
        _loaded_objects=[expected_tab],
    )

    actual_tab = manager.get_or_open(
        url="https://www.google.com",
        wait_until_loaded=True,
        preserve_focus=False,
    )

    assert actual_tab is expected_tab
    assert existing_tab.wait_calls == 1


def test_window_tabs_get_or_open_opens_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    expected_tab = cast("ChromeTab", object())
    calls: list[tuple[str, bool, bool]] = []

    def fake_open(
        self: ChromeWindowTabsManager,
        url: str,
        *,
        wait_until_loaded: bool = True,
        preserve_focus: bool = True,
    ) -> ChromeTab:
        calls.append((url, wait_until_loaded, preserve_focus))
        return expected_tab

    monkeypatch.setattr(ChromeWindowTabsManager, "open", fake_open)
    manager = ChromeWindowTabsManager(
        from_window=cast("ChromeWindow", object()),
        _loaded=True,
        _loaded_objects=[],
    )

    actual_tab = manager.get_or_open(
        url="https://www.google.com",
        wait_until_loaded=False,
        preserve_focus=False,
    )

    assert actual_tab is expected_tab
    assert calls == [("https://www.google.com", False, False)]


def test_windows_tabs_get_or_open_returns_existing_tab() -> None:
    existing_tab = FakeTab(url="https://www.google.com")
    expected_tab = cast("ChromeTab", existing_tab)
    manager = ChromeWindowsTabsManager(
        from_windows=cast("ChromeWindowsManager", object()),
        _loaded=True,
        _loaded_objects=[expected_tab],
    )

    actual_tab = manager.get_or_open(
        url="https://www.google.com",
        wait_until_loaded=True,
        preserve_focus=False,
    )

    assert actual_tab is expected_tab
    assert existing_tab.wait_calls == 1


def test_windows_tabs_get_or_open_opens_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    expected_tab = cast("ChromeTab", object())
    calls: list[tuple[str, bool, bool]] = []

    def fake_open(
        self: ChromeWindowsTabsManager,
        url: str,
        *,
        wait_until_loaded: bool = True,
        preserve_focus: bool = True,
    ) -> ChromeTab:
        calls.append((url, wait_until_loaded, preserve_focus))
        return expected_tab

    monkeypatch.setattr(ChromeWindowsTabsManager, "open", fake_open)
    manager = ChromeWindowsTabsManager(
        from_windows=cast("ChromeWindowsManager", object()),
        _loaded=True,
        _loaded_objects=[],
    )

    actual_tab = manager.get_or_open(
        url="https://www.google.com",
        wait_until_loaded=False,
        preserve_focus=False,
    )

    assert actual_tab is expected_tab
    assert calls == [("https://www.google.com", False, False)]
