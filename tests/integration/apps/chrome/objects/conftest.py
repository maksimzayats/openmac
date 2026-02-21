from __future__ import annotations

import pytest

from openmac.apps.chrome.objects.application import Chrome


@pytest.fixture(scope="module")
def chrome() -> Chrome:
    chrome = Chrome()
    _ = chrome.version

    return chrome
