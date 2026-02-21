from __future__ import annotations

import pytest

from openmac.apps.chrome.objects.application import Chrome
from openmac.apps.chrome.objects.tabs import Tab


@pytest.fixture(scope="function")
def tab(chrome: Chrome) -> Tab:
    return chrome.windows.first().tabs.first()


def test_tabs_properties_complete(tab: Tab) -> None:
    properties = tab.properties
    properties_keys = set(properties.__dataclass_fields__.keys())

    ae_properties = tab._ae_object.properties()
    ae_properties_keys = {keyword.AS_name for keyword in ae_properties}

    ae_properties_keys.remove("URL")
    ae_properties_keys.add("url")

    diff = properties_keys.symmetric_difference(ae_properties_keys)

    assert diff == {"class_"}
