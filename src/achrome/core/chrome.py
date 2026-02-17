from __future__ import annotations

from achrome.core._internal.apple_script import AppleScriptRunner
from achrome.core._internal.context import Context
from achrome.core.tabs import Tab, TabsManager
from achrome.core.windows import WindowsManager


class Chrome:
    def __init__(self) -> None:
        self._context = Context(runner=AppleScriptRunner())

    @property
    def windows(self) -> WindowsManager:
        return WindowsManager(_context=self._context)

    @property
    def tabs(self) -> TabsManager:
        tabs: list[Tab] = []
        for window in self.windows:
            tabs.extend(window.tabs.items)

        return TabsManager(_context=self._context, _items=tabs)


def main() -> None:
    chrome = Chrome()

    for window in chrome.windows:
        print(f"Window: {window.name} (id={window.id})")
        for tab in window.tabs:
            print(f"  Tab: {tab.name} (id={tab.id}, url={tab.url}, wid={tab.window_id})")


if __name__ == "__main__":
    main()
