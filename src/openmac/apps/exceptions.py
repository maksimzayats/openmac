from __future__ import annotations

from openmac.exceptions import OpenMacError


class OpenMacAppError(OpenMacError):
    """Base class for all OpenMac app exceptions."""


class ObjectDoesNotExistError(OpenMacAppError):
    """Raised when a manager `.get()` query returns no objects."""


class MultipleObjectsReturnedError(OpenMacAppError):
    """Raised when a manager `.get()` query returns multiple objects."""


class InvalidFilterError(OpenMacAppError):
    """Raised when filter criteria references an unsupported lookup or field."""
