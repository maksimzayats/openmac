from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager

from appscript import app, its


@contextmanager
def preserve_focus(delay: float = 0.05) -> Iterator[None]:
    """Preserve the currently frontmost macOS application and restore it after the wrapped block finishes."""
    system_events = app("System Events")

    front_bundle: str = system_events.processes[its.frontmost == True].first.bundle_identifier.get()  # noqa: E712

    try:
        yield
    finally:
        # Small delay prevents activation race issues
        if delay > 0:
            time.sleep(delay)

        app(id=front_bundle).activate()
