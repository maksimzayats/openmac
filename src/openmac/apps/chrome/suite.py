from __future__ import annotations

from typing import Any

from appscript import app


class Chrome:
    def __init__(self) -> None:
        self._app = app("Google Chrome")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._app, name)()


chrome = Chrome()
print(chrome.version)
