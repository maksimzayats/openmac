from __future__ import annotations

from appscript import app

from openmac.apps._internal.base import BaseApplication


class Chrome(BaseApplication):
    def __init__(self) -> None:
        self._app = app(id="com.google.Chrome")

    @property
    def version(self) -> str:
        return self._app.version()
