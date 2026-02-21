from __future__ import annotations

import pytest

from openmac.apps.chrome.objects.application import Chrome
from openmac.apps.chrome.objects.windows import ChromeWindow


@pytest.fixture(scope="function")
def window(chrome: Chrome) -> ChromeWindow:
    return chrome.windows.first


def test_window_properties_complete(window: ChromeWindow) -> None:
    properties = window.properties
    properties_keys = set(properties.__dataclass_fields__.keys())

    ae_properties = window._ae_object.properties()
    ae_properties_keys = {keyword.AS_name for keyword in ae_properties}

    diff = properties_keys.symmetric_difference(ae_properties_keys)

    assert diff == {"class_"}
