from __future__ import annotations

from openmac.apps.browsers.safari.objects.application import Safari
from openmac.apps.browsers.safari.objects.documents import (
    SafariDocument,
    SafariDocumentsManager,
)
from openmac.apps.browsers.safari.objects.tabs import (
    SafariTab,
    SafariWindowsTabsManager,
    SafariWindowTabsManager,
)
from openmac.apps.browsers.safari.objects.windows import (
    SafariWindow,
    SafariWindowsManager,
)

__all__ = [
    "Safari",
    "SafariDocument",
    "SafariDocumentsManager",
    "SafariTab",
    "SafariWindow",
    "SafariWindowTabsManager",
    "SafariWindowsManager",
    "SafariWindowsTabsManager",
]
