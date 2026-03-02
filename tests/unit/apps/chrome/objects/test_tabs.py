from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from openmac.apps.browsers.chrome.objects.tabs import ChromeTab, ChromeWindowsTabsManager

if TYPE_CHECKING:
    from openmac.apps.browsers.chrome.objects.windows import ChromeWindowsManager


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
