from __future__ import annotations

from openmac.apps.browsers.chrome.objects.application import Chrome, ChromeProperties
from openmac.apps.browsers.chrome.objects.bookmark_folders import (
    ChromeBookmarkFolder,
    ChromeBookmarkFolderProperties,
    ChromeBookmarkFoldersManager,
    ChromeBookmarkItemsManager,
)
from openmac.apps.browsers.chrome.objects.bookmark_items import (
    ChromeBookmarkItem,
    ChromeBookmarkItemProperties,
)
from openmac.apps.browsers.chrome.objects.tabs import (
    ChromeTab,
    ChromeTabProperties,
    ChromeWindowsTabsManager,
    ChromeWindowTabsManager,
)
from openmac.apps.browsers.chrome.objects.windows import (
    ChromeWindow,
    ChromeWindowProperties,
    ChromeWindowsManager,
)

__all__ = [
    "Chrome",
    "ChromeBookmarkFolder",
    "ChromeBookmarkFolderProperties",
    "ChromeBookmarkFoldersManager",
    "ChromeBookmarkItem",
    "ChromeBookmarkItemProperties",
    "ChromeBookmarkItemsManager",
    "ChromeProperties",
    "ChromeTab",
    "ChromeTabProperties",
    "ChromeWindow",
    "ChromeWindowProperties",
    "ChromeWindowTabsManager",
    "ChromeWindowsManager",
    "ChromeWindowsTabsManager",
]
