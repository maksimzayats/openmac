from __future__ import annotations


class AChromeError(Exception):
    """Base class for all AChrome exceptions."""


class DoesNotExistError(AChromeError):
    """Raised when a manager `.get()` query returns no objects."""


class MultipleObjectsReturnedError(AChromeError):
    """Raised when a manager `.get()` query returns multiple objects."""
