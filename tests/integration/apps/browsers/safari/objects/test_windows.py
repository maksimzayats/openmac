from __future__ import annotations

from collections.abc import Generator
from contextlib import suppress

import pytest
from appscript import CommandError

from openmac.apps.browsers.safari.objects.application import Safari
from openmac.apps.browsers.safari.objects.windows import SafariWindow


@pytest.fixture(scope="function")
def window(safari: Safari) -> Generator[SafariWindow]:
    window = safari.windows.new(url="https://www.google.com", preserve_focus=False)
    window.current_tab.wait_until_loaded()

    try:
        yield window
    finally:
        with suppress(CommandError):
            window.close()
