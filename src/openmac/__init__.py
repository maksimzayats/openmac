from __future__ import annotations

from openmac.apps.browsers.base.objects.application import IBrowser
from openmac.apps.browsers.base.objects.tabs import IBrowserTab
from openmac.apps.browsers.base.objects.windows import IBrowserWindow
from openmac.apps.browsers.chrome.objects.application import Chrome
from openmac.apps.browsers.chrome.objects.bookmark_folders import (
    ChromeBookmarkFolder,
    ChromeBookmarkFoldersManager,
)
from openmac.apps.browsers.chrome.objects.tabs import ChromeTab
from openmac.apps.browsers.chrome.objects.windows import ChromeWindow
from openmac.apps.browsers.safari.objects.application import Safari
from openmac.apps.browsers.safari.objects.documents import SafariDocument
from openmac.apps.browsers.safari.objects.tabs import SafariTab
from openmac.apps.browsers.safari.objects.windows import SafariWindow

__all__: list[str] = [
    "Chrome",
    "ChromeBookmarkFolder",
    "ChromeBookmarkFoldersManager",
    "ChromeTab",
    "ChromeWindow",
    "IBrowser",
    "IBrowserTab",
    "IBrowserWindow",
    "Safari",
    "SafariDocument",
    "SafariTab",
    "SafariWindow",
]
