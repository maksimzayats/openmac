from __future__ import annotations

from dataclasses import dataclass

from appscript import Keyword

from openmac.apps._internal.base import BaseApplication
from openmac.apps.chrome.objects.window import Window, WindowsManager


class Chrome(BaseApplication):
    _BUNDLE_ID = "com.google.Chrome"

    @property
    def version(self) -> str:
        return self._ae_object.version()

    @property
    def title(self) -> str:
        return self._ae_object.title()

    @property
    def frontmost(self) -> bool:
        return self._ae_object.frontmost()

    @property
    def properties(self) -> ChromeProperties:
        ae_properties = self._ae_object.properties()
        print(ae_properties)
        return ChromeProperties(
            version=ae_properties[Keyword("version")],
            title=ae_properties[Keyword("title")],
            frontmost=ae_properties[Keyword("frontmost")],
        )

    @property
    def windows(self) -> WindowsManager:
        return WindowsManager(
            _objects=[Window(_ae_object=ae_window) for ae_window in self._ae_object.windows()],
        )


@dataclass(slots=True)
class ChromeProperties:
    version: str
    title: str
    frontmost: bool


chrome = Chrome()
for w in chrome.windows.filter(tabs__url__contains="google"):
    print(w.properties)
    for t in w.tabs:
        print("  ", t.properties)
