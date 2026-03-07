from __future__ import annotations

from openmac.apps.browsers.safari.objects.application import Safari, SafariProperties
from openmac.apps.browsers.safari.objects.documents import (
    SafariDocument,
    SafariDocumentProperties,
    SafariDocumentsManager,
)
from openmac.apps.browsers.safari.objects.tabs import (
    SafariTab,
    SafariTabProperties,
    SafariWindowsTabsManager,
    SafariWindowTabsManager,
)
from openmac.apps.browsers.safari.objects.windows import (
    SafariWindow,
    SafariWindowProperties,
    SafariWindowsManager,
)

__all__ = [
    "Safari",
    "SafariDocument",
    "SafariDocumentProperties",
    "SafariDocumentsManager",
    "SafariProperties",
    "SafariTab",
    "SafariTabProperties",
    "SafariWindow",
    "SafariWindowProperties",
    "SafariWindowTabsManager",
    "SafariWindowsManager",
    "SafariWindowsTabsManager",
]
