from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager, suppress

from appscript import CommandError, app, its

logger = logging.getLogger(__name__)


@contextmanager
def preserve_focus(delay: float = 0.05) -> Iterator[None]:
    """Preserve the currently frontmost macOS application and restore it after the wrapped block finishes."""
    system_events = app("System Events")

    front_bundle: str = system_events.processes[its.frontmost == True].first.bundle_identifier.get()  # noqa: E712
    logger.debug(
        "Preserving focus for frontmost application bundle=%s with restore delay=%s",
        front_bundle,
        delay,
    )

    try:
        yield
    finally:
        # Small delay prevents activation race issues
        if delay > 0:
            logger.debug(
                "Waiting %s seconds before restoring focus to bundle=%s",
                delay,
                front_bundle,
            )
            time.sleep(delay)

        with suppress(CommandError, OSError):
            logger.debug("Restoring focus to original application bundle=%s", front_bundle)
            app(id=front_bundle).activate()
