from __future__ import annotations


class OpenMacError(Exception):
    """Base class for all OpenMac exceptions."""


class ObjectDoesNotExistError(OpenMacError):
    """Raised when a manager `.get()` query returns no objects."""


class MultipleObjectsReturnedError(OpenMacError):
    """Raised when a manager `.get()` query returns multiple objects."""
