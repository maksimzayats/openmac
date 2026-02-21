from __future__ import annotations

import pytest

from openmac.apps.chrome.application import Chrome
from tests.integration.apps.helpers import get_app_properties, get_apple_script_properties


@pytest.fixture(scope="module")
def chrome() -> Chrome:
    return Chrome()


def test_application_properties(chrome: Chrome) -> None:
    apple_script_properties = get_apple_script_properties(chrome)
    chrome_properties = get_app_properties(chrome)

    diff = apple_script_properties.difference(chrome_properties)

    assert diff == {"class_"}
