from __future__ import annotations

import pytest

from openmac import Safari
from openmac.apps.browsers.chrome.objects.application import Chrome


@pytest.fixture(scope="module")
def chrome() -> Chrome:
    chrome = Chrome()
    _ = chrome.version

    return chrome


@pytest.fixture(scope="module")
def safari() -> Safari:
    safari = Safari()
    _ = safari.version

    return safari
