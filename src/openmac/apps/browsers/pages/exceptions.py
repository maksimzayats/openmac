from __future__ import annotations

from openmac.apps.exceptions import OpenMacAppError


class OpenMacBrowserPageError(OpenMacAppError):
    """Base class for all OpenMac browser page exceptions."""


class InternalBrowserPageError(OpenMacBrowserPageError):
    """Raised when an openmac browser page encounters an internal error."""


class InvalidDataError(InternalBrowserPageError):
    """Raised when a openmac browser page encounters invalid data."""
