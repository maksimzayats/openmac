from __future__ import annotations

import pytest

from openmac.apps.chrome.objects import Chrome
from tests.integration.apps.helpers import get_app_properties, get_apple_script_properties


@pytest.fixture(scope="module")
def chrome() -> Chrome:
    return Chrome()


def test_application_properties(chrome: Chrome) -> None:
    apple_script_properties = get_apple_script_properties(
        chrome,
        mapping={"URL": "url"},
    )

    chrome_properties = get_app_properties(chrome)

    diff = apple_script_properties.difference(chrome_properties)

    assert diff == {"class_", "id"}


def test_bookmarks_bar_properties(chrome: Chrome) -> None:
    apple_script_properties = get_apple_script_properties(
        chrome.bookmarks_bar,
        mapping={"URL": "url"},
    )

    print(apple_script_properties)

    chrome_properties = get_app_properties(chrome)

    diff = apple_script_properties.difference(chrome_properties)

    assert diff == 1123
